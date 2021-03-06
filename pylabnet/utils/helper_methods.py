def str_to_float(in_val):
    """Convert human-readable exponential form to float.

    :param in_val: (str) input string of the following formats:

            'float_number' --> float_number

            'float_number + white_space + exp_prefix + unit_string'
                                 --> float_number * 10**exp_value

        Supported exp prefixes: ['T', 'G', 'M', 'k', '', 'm', 'u', 'n', 'p']

        Warning: format 'just exp_prefix without unit_string' is not
        supported: if only one symbol is given after 'float_number',
        it will be interpreted as unit and exponent will be set to 10**0.

        Examples: '1.2 us'   --> 1.2e-6
                  '-4.5 mV'  --> -4.5e-3
                  '10.1 GHz' --> 1.01e10
                  '1.56 s'   --> 1.56
                  '1.56 m'   --> 1.56 [interpreted as 1.56 meters, not as 1.56e-3]

    :return: (float) extracted value without unit
    """

    if isinstance(in_val, (float, int)):
        return in_val

    # Split string into mantissa and exp_prefix + unit
    item_list = in_val.split()

    # Extract mantissa exp_prefix if included
    mantissa = float(item_list[0])
    # Extract exp_prefix (a single letter) if included
    try:
        exp_prefix_unit = item_list[1]

        if len(exp_prefix_unit) > 1:
            exp_prefix = item_list[1][0]
        else:
            exp_prefix = ''

    except IndexError:
        exp_prefix = ''

    # Convert exp_prefix into exp_value
    if exp_prefix == 'T':
        exp_value = 12
    elif exp_prefix == 'G':
        exp_value = 9
    elif exp_prefix == 'M':
        exp_value = 6
    elif exp_prefix == 'k':
        exp_value = 3
    elif exp_prefix == '':
        exp_value = 0
    elif exp_prefix == 'm':
        exp_value = -3
    elif exp_prefix == 'u':
        exp_value = -6
    elif exp_prefix == 'n':
        exp_value = -9
    elif exp_prefix == 'p':
        exp_value = -12
    else:
        # The case of multi-letter unit without prefix: '1.5 Hz'
        # the first letter 'H' is not an exp prefix
        exp_value = 0

    return mantissa * (10 ** exp_value)


def pwr_to_float(in_val):

    # FIXME: implement

    # if isinstance(in_val, float):
    #     return in_val
    # #
    # # Determine whether the power is given in Volts or dBm
    # #
    # # Split string into mantissa and exp_prefix + unit
    # item_list = in_val.split()
    #
    # # Extract exp_prefix (a single letter) if included
    # try:
    #     exp_prefix_unit = item_list[1]
    #
    #     if len(exp_prefix_unit) > 1:
    #         exp_prefix = item_list[1][0]
    #     else:
    #         exp_prefix = ''
    # except IndexError:
    #     exp_prefix = ''

    return str_to_float(in_val=in_val)



