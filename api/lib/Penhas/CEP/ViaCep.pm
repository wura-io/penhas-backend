package Penhas::CEP::ViaCep;

use Moose::Role;
use feature 'state';

use Furl;
use JSON qw(decode_json);

sub name {'ViaCep'}

sub _find {
    state $ua = Furl->new(timeout => 20);

    my $cep = pop;
    my $res = $ua->get('https://viacep.com.br/ws/' . $cep . '/json/');

    die sprintf 'ViaCep request failed for cep %s: HTTP %s', $cep, $res->code
      unless $res->is_success;

    my $r = eval { decode_json($res->content) };
    die sprintf 'ViaCep returned invalid JSON for cep %s: %s', $cep, $@
      if $@ || !$r;

    return if $r->{erro};

    my $street = $r->{logradouro} || '';

    return {street => $street, city => $r->{localidade}, district => $r->{bairro}, state => $r->{uf},
        ibge => $r->{ibge}};
}

1;
