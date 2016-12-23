import argparse
from pathlib import Path

from aiohttp_admin.layout_utils import generate_config


def build_parser():
    ap = argparse.ArgumentParser()
    subparsers = ap.add_subparsers(help='commands', dest="cmd_name")

    gen_parser = subparsers.add_parser(
        'ng', help='Generate basic js code for admin views')
    gen_parser.add_argument('-b', '--bare', action='store',
                            help='Generate bare config.js file')
    return ap


def ng(params):
    path = Path(params.bare)
    print(path.absolute())
    js = generate_config([], 'admin')
    with open(str(path / 'config.js'), 'w') as f:
        f.write(js)


def main(args=None):
    ap = build_parser()
    params = ap.parse_args(args)
    if params.cmd_name == 'ng':
        ng(params)


if __name__ == "__main__":
    main()
