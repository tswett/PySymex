from symex import SAtom, Symex

def test_can_parse_an_atom():
    result = Symex.parse('test')
    assert result == SAtom('test')