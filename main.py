from maseya import z3pr


def main(argv=None):
    options = z3pr.get_options_from_anywhere(argv, "args.config")
    z3pr.randomize_from_options(options)


if __name__ == "__main__":
    main()
