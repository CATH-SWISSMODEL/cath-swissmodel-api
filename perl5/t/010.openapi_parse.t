use Mojo::Base -strict;
use Test::More;
use Mojolicious::Lite;

use FindBin;
use Path::Tiny;

my $spec_dir = path( "$FindBin::Bin/../../api/" );
my @spec_files = $spec_dir->children( qr/\.(json|yml)$/ );

for my $spec_file ( @spec_files ) {
    diag( "Testing spec: $spec_file ... " );
    eval { plugin OpenAPI => {url => $spec_file->absolute} };
    ok( !$@, sprintf( "validated %s okay", $spec_file->basename ) ) or diag $@;
}

done_testing();