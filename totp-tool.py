#!/usr/bin/env python3

#
# Copyright 2019 me@sigsec.net
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

#
# TOTP two-factor authentication tool. Used to output the current code for a
# TOTP seed and generate QR codes. Related article here:
#   https://blog.sigsec.net/posts/2019/09/two-factor-totp-codes.html
# 
# You will need the 'pyotp' and 'pyqrcode' modules installed to use this.
#


import argparse
import sys
from datetime import datetime, timedelta

import pyotp
import pyqrcode


_DESCRIPTION = """
Manipulate TOTP-based two-factor authorisation codes.

Either provide an existing seed or use the --new argument to generate a new one.
The program will output the TOTP seed, the current time and the current check
value for the code. Passing --extra-codes will output the two codes on either
side of the current one, in case clocks are out of sync.

A QR code can generated; to do this, provide the --draw argument. The QR code
contains a user name and an issuer name, these can be provided if desired. The
QR can also be scaled up using  --upscale.

eg:
  ./totp-tool.py -nd --qr-issuer="sigsec" --qr-user="me@sigsec.net"

"""


def build_provisioning_qrc(totp: pyotp.TOTP, user_name: str, issuer_name: str) -> pyqrcode.QRCode:
    totp_url = totp.provisioning_uri(user_name, issuer_name)
    return pyqrcode.create(totp_url)


def draw_token_manual_2x(qrc: pyqrcode.QRCode):
    quiet_zone = '██' * (4 + len(qrc.code[0]))

    print()
    print(quiet_zone)
    print(quiet_zone)
    for row in qrc.code:
        print('████' + ''.join(['██', '  '][_] for _ in row) + '████')

    print(quiet_zone)
    print(quiet_zone)
    print()


def draw_token_manual(qrc: pyqrcode.QRCode):
    #  ▄▀█

    quiet_zone = '█' * (4 + len(qrc.code[0]))
    print_this_row = False
    row_buffer = ['█'] * (len(qrc.code[0]))

    print()
    print(quiet_zone)
    for row in qrc.code:

        for i, cell in enumerate(row):
            if not cell:
                continue

            if not print_this_row:
                row_buffer[i] = '▄'
            elif row_buffer[i] == '▄':
                row_buffer[i] = ' '
            else:
                row_buffer[i] = '▀'

        if print_this_row:
            print('██' + ''.join(row_buffer) + '██')
            row_buffer = ['█'] * (len(qrc.code[0]))

        print_this_row = not print_this_row

    if print_this_row:
        # We had an odd number of rows.
        print('██' + ''.join(row_buffer) + '██')

    print(quiet_zone)
    print()


def print_code(totp: pyotp.TOTP, time_delta: int = 0):
    dt = datetime.now()

    if time_delta != 0:
        dt = dt + timedelta(seconds=time_delta)

    print("At %s, the check code is: %s" % (
        dt.strftime("%H:%M:%S"),
        totp.at(dt)
    ))


def main(args: argparse.Namespace) -> int:
    if args.new and args.token:
        sys.stderr.write("Either specify a token or use --new/-n, but not both\n")
        return 1
    if not args.new and not args.token:
        sys.stderr.write("No arguments provided. Call with --help for operating instructions\n")
        return 1

    if args.new:
        totp_key = pyotp.random_base32()
    elif args.token:
        totp_key = args.token

    totp = pyotp.TOTP(totp_key)
    print("Using the TOTP seed: %s" % totp_key)

    if args.extra_codes:
        print_code(totp, -60)
        print_code(totp, -30)
    print_code(totp)
    if args.extra_codes:
        print_code(totp, +30)
        print_code(totp, +60)

    if args.draw:
        qrc = build_provisioning_qrc(totp, args.qr_user, args.qr_issuer)

        if args.upscale:
            draw_token_manual_2x(qrc)
        else:
            draw_token_manual(qrc)

    return 0


def _get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=_DESCRIPTION,
        formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument(
        'token', type=str, nargs='?',
        help='Use an existing token (or use --new)')
    parser.add_argument(
        '--new', '-n', action='store_true',
        help='Generate a new token (or provide a token)')

    parser.add_argument(
        '--extra-codes', '-x', action='store_true',
        help='Also generate the two previous codes and the two next codes')

    drawing_group = parser.add_argument_group('Drawing')
    drawing_group.add_argument(
        '--draw', '-d', action='store_true',
        help='Draw a QR code of the token')
    drawing_group.add_argument(
        '--upscale', action='store_true',
        help='Draw at 2x scale')
    drawing_group.add_argument(
        '--qr-user', type=str, metavar='user', default='user@example.com',
        help='The username to be encoded in the QR code')
    drawing_group.add_argument(
        '--qr-issuer', type=str, metavar='issuer', default='Example Corp',
        help='The issuer to be encoded in the QR code')
    

    return parser.parse_args()


if __name__ == '__main__':
    sys.exit(main(_get_args()))
