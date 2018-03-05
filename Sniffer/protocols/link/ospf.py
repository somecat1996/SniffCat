#!/usr/bin/python3
# -*- coding: utf-8 -*-


# Open Shortest Path First
# Analyser for OSPF header


from .link import Link
from ..utilities import Info


# OSPF Packet Types
TYPE = {
    1 : 'Hello',
    2 : 'Database Description',
    3 : 'Link State Request',
    4 : 'Link State Update',
    5 : 'Link State Acknowledgment',
}


# Authentication Types
AUTH = {
    0 : 'Null Authentication',
    1 : 'Simple Password',
    2 : 'Cryptographic Authentication',
}


class OSPF(Link):
    """This class implements Open Shortest Path First.

    Properties:
        * name -- str, name of corresponding procotol
        * info -- Info, info dict of current instance
        * layer -- str, `Link`
        * length -- int, header length of corresponding protocol
        * protochain -- ProtoChain, protocol chain of current instance
        * type -- str, OSPF packet type

    Methods:
        * read_ospf -- read Open Shortest Path First

    Attributes:
        * _file -- BytesIO, bytes to be extracted
        * _info -- Info, info dict of current instance
        * _protos -- ProtoChain, protocol chain of current instance

    Utilities:
        * _read_protos -- read next layer protocol type
        * _read_fileng -- read file buffer
        * _read_unpack -- read bytes and unpack to integers
        * _read_binary -- read bytes and convert into binaries
        * _decode_next_layer -- decode next layer protocol type
        * _import_next_layer -- import next layer protocol extractor
        * _read_id_numbers -- read router and area IDs
        * _read_encrypt_auth -- read Authentication field when CA employed

    """
    ##########################################################################
    # Properties.
    ##########################################################################

    @property
    def name(self):
        return 'Open Shortest Path First'

    @property
    def length(self):
        return 24

    @property
    def type(self):
        return self._info.type

    ##########################################################################
    # Methods.
    ##########################################################################

    def read_ospf(self, length):
        """Read Open Shortest Path First.

        Structure of OSPF header [RFC 2328]:

            0                   1                   2                   3
            0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
           +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
           |   Version #   |     Type      |         Packet length         |
           +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
           |                          Router ID                            |
           +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
           |                           Area ID                             |
           +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
           |           Checksum            |             AuType            |
           +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
           |                       Authentication                          |
           +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
           |                       Authentication                          |
           +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

            Octets          Bits          Name                Discription
              0              0          ospf.version      Version #
              1              8          ospf.type         Type (0/1)
              2              16         ospf.len          Packet Length (header includes)
              4              32         ospf.router_id    Router ID
              8              64         ospf.area_id      Area ID
              12             96         ospf.chksum       Checksum
              14             112        ospf.autype       AuType
              16             128        ospf.auth         Authentication

        """
        _vers = self._read_unpack(1)
        _type = self._read_unpack(1)
        _tlen = self._read_unpack(2)
        _rtid = self._read_id_numbers()
        _area = self._read_id_numbers()
        _csum = self._read_fileng(2)
        _autp = self._read_unpack(2)

        ospf = dict(
            version = _vers,
            type = TYPE.get(_type),
            len = _tlen,
            router_id = _rtid,
            area_id = _area,
            chksum = _csum,
            autype = AUTH.get(_autp) or 'Reserved',
        )

        if _autp == 2:
            ospf['auth'] = self._read_encrypt_auth()
        else:
            ospf['auth'] = self._read_fileng(8)

        length = ospf['len'] - 24
        return self._decode_next_layer(ospf, length)

    ##########################################################################
    # Data models.
    ##########################################################################

    def __init__(self, _file, length=None):
        self._file = _file
        self._info = Info(self.read_ospf(length))

    def __len__(self):
        return 24

    def __length_hint__(self):
        return 24

    ##########################################################################
    # Utilities.
    ##########################################################################

    def _read_id_numbers(self):
        """Read router and area IDs."""
        _byte = self._read_fileng(4)
        _addr = '.'.join([str(_) for _ in _byte])
        return _addr

    def _read_encrypt_auth(self):
        """Read Authentication field when Cryptographic Authentication is employed.

        Structure of Cryptographic Authentication [RFC 2328]:

            0                   1                   2                   3
            0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
           +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
           |              0                |    Key ID     | Auth Data Len |
           +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
           |                 Cryptographic sequence number                 |
           +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

            Octets          Bits          Name                Discription
              0              0          ospf.auth.resv    Reserved (must be zero)
              2              16         ospf.auth.key_id  Key ID
              3              24         ospf.auth.len     Auth Data Length
              4              32         ospf.auth.seq     Cryptographic Aequence Number

        """
        _resv = self._read_fileng(2)
        _keys = self._read_unpack(1)
        _alen = self._read_unpack(1)
        _seqn = self._read_unpack(4)

        auth = dict(
            resv = _resv,
            key_id = _keys,
            len = _alen,
            seq = _seqn,
        )

        return auth
