use strict;
use warnings;
use ExtUtils::MakeMaker;

# Normalize version strings like 6.30_02 to 6.3002,
# so that we can do numerical comparisons on it.
my $eumm_version = $ExtUtils::MakeMaker::VERSION;
$eumm_version =~ s/_//;

WriteMakefile(
    NAME                => 'CATH::API::Model',
    AUTHOR              => q{Ian Sillitoe <i.sillitoe@ucl.ac.uk>},
    VERSION_FROM        => 'lib/Cath/API/Model.pm',
    ABSTRACT            => 'Interface for the CATH 3D Model API',
    ($eumm_version >= 6.3001
      ? ('LICENSE'=> 'perl')
      : ()),
    PL_FILES            => {},
    PREREQ_PM => {
        'local::lib'                   => '2.00',
        'Test::More'                   => '0.88',
        'Mojolicious'                  => '7.82',
        'Mojolicious::Plugin::OpenAPI' => '1.30',
    },
    dist                => { COMPRESS => 'gzip -9f', SUFFIX => 'gz', },
    clean               => { FILES => 'Cath-*' },
);
