#!/bin/bash
#
# Usage:
#   $ deploy.sh { dev | staging | prod } init
#   $ deploy.sh { dev | staging | prod } update

# die on any error
set -e

CATHAPI_LATEST_TAG="v0.0.1"
CATHAPI_SOURCE="https://github.com/CATH-SWISSMODEL/cath-swissmodel-api.git"

NGINX_BASE=/etc/nginx
VHOSTS_BASE=/var/www/vhosts
DEBUG_FLAG=0

if [[ $# -eq 0 ]]; then
    echo "Usage:"
    echo "    deploy.sh { dev | staging | prod } init"
    echo "    deploy.sh { dev | staging | prod } update"
    echo
    exit 0
fi

RELEASE="$1"
ACTION="$2"
CATHAPI_BRANCH=""

case "$RELEASE" in
    dev)
        ;;
    staging)
        CATHAPI_BRANCH="--branch=${CATHAPI_TAG:-$CATHAPI_LATEST_TAG}"
        ;;
    prod)
        CATHAPI_BRANCH="--branch=${CATHAPI_TAG:-$CATHAPI_LATEST_TAG}"
        ;;
    *)
        echo "unknown release type: $RELEASE (expected < dev | staging | prod >)"
        exit 1
esac

BASEDIR=$VHOSTS_BASE/cathapi-${RELEASE}
USER=$(whoami)

CATHAPI_DIR=$BASEDIR/cath-swissmodel-api

echo
echo "#####################################################"
echo "# CATH API deployment"
echo "#####################################################"
echo "# ACTION         $ACTION"
echo "# RELEASE        $RELEASE"
echo "# BASEDIR        $BASEDIR"
echo "# CATHAPI_SOURCE $CATHAPI_SOURCE"
echo "# CATHAPI_BRANCH $CATHAPI_BRANCH"
echo "# CATHAPI_DIR    $CATHAPI_DIR"
echo "#####################################################"
echo

function update_code {
    if [ -d "$CATHAPI_DIR" ]; then
        echo "Refreshing existing CATHAPI code from $CATHAPI_SOURCE ..."
        (set -x; cd $CATHAPI_DIR; git pull; git checkout $CATHAPI_BRANCH)
    else
        echo "Clone new CATHAPI code from $CATHAPI_SOURCE ..."
        (set -x; git clone $CATHAPI_BRANCH $CATHAPI_SOURCE $CATHAPI_DIR)
    fi
    echo "  ... done"
    echo
}

function update {
    update_code

    HTTP_SITECONF_FILENAME=cathapi-${RELEASE}.conf
    HTTP_SITECONF_SRC=$HTTP_BASE/sites-available/$HTTP_SITECONF_FILENAME
    HTTP_SITECONF_LINK=$HTTP_BASE/sites-enabled/$HTTP_SITECONF_FILENAME
    if [ ! -e $HTTP_SITECONF_SRC ]; then
        echo "HTTP config file does not exist: $HTTP_SITECONF_SRC"
        exit 5
    fi

    if [ ! -e $HTTP_SITECONF_LINK ]; then
        echo "Adding link for site config ... "
        (set -x; sudo cd $HTTP_BASE/sites-enabled/ && sudo ln -s ../sites-available/$HTTP_SITECONF_FILENAME .)
    fi

    echo "Restarting httpd (requires sudo) ... "
    (set -x; sudo systemctl restart httpd)
    echo "  ... done"
    echo
}

# do one-off stuff
function init {

    echo "Making sure app dir '$BASEDIR' exists and is owned by $USER ... (requires sudo)"
    (set -x; sudo mkdir -p $BASEDIR && sudo chown -R $USER:users $BASEDIR)
    echo "  ... done"
    echo 

    update_code
    update_web

    echo "Setting up httpd service (requires sudo) ... "
    (set -x; sudo systemctl enable httpd && sudo systemctl start httpd)
    echo "  ... done"
    echo

    APPDIR=$BASEDIR/cath-swissmodel-api/cathapi

    SECRET_KEY_FILE=$APPDIR/cathapi/secret_key.txt
    if [ ! -e $SECRET_KEY_FILE ]; then
        echo "Generating Django secret key ... " 
        DJANGO_SECRET_KEY=`openssl rand -base64 48`
        if [ $? -ne 0 ]; then
            echo "Error creating secret key."
            exit 3
        fi
        echo $DJANGO_SECRET_KEY > $SECRET_KEY_FILE
        echo "  ... done"
        echo
    fi

    echo "Installing Python ... "
    (set -x; sudo yum install centos-release-scl rh-python36 rh-python36-python-devel rh-python36-mod_wsgi)

    VENV_DIR=$APPDIR/venv
    if [ ! -d "$VENV_DIR" ]; then
        echo "Installing Python environment ... "
        (set -x; cd $APPDIR && scl enable rh-python36 python -m venv venv)
        echo "  ... done"
        echo
    fi

    echo "Updating Python environment ... "
    (source $APPDIR/venv/bin/activate; set -x; \
        pip install -q --upgrade pip \
        && pip install -q -r $APPDIR/requirements-to-freeze.txt )
    echo "  ... done"
    echo

    HTTP_WSGI_MODULE_FILE=$HTTP_BASE/conf.modules.d/10-wsgi.conf
    if [ ! -f $HTTP_WSGI_MODULE_FILE ]; then
        echo "Creating WSGI MODULE file ... "
        #pip install mod_wsgi
        (source $APPDIR/venv/bin/activate; set -x; \
            mod_wsgi-express module-config > $HTTP_WSGI_MODULE_FILE)
        echo "  ... done"
        echo
    fi
}

case "$ACTION" in
    init)
        echo "Initialising deployment ..."
        init
        ;;
    update)
        echo "Updating existing deployment ..."
        update
        ;;
    info)
        ;;
    *)
        echo "Error: unknown action '$ACTION'"
        exit 2
        ;;
esac

echo
echo "DONE"
