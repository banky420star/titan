import argparse

def main(args):
    print(f'Hello from Titan, {args.name}!')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--name', default='World', help='Your name')
    args = parser.parse_args()
    main(args)