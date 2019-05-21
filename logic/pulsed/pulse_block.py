import numpy as np
import copy


class PulseBlock:
    def __init__(self, *p_obj_list, name=''):
        # p_obj_list = [
        #     po.High(chnl='ch1', t=0, dur=1e-6),
        #     po.Sin(chnl='ch2', t=1e-6, dur=1e-6, amp=1e-3, freq=2.5e9, ph=0)
        # ]

        # p_dict = {
        #     'ch1': [
        #         PulseObject(ch, t=0, dur, ...),
        #         PulseObject(ch, t=0, dur, ...),
        #         PulseObject(ch, t=0, dur, ...)
        #     ],
        #     'ch3': [
        #         PulseObject(ch, t=0, dur, ...),
        #         PulseObject(ch, t=0, dur, ...)
        #     ],
        #
        # }

        self.name = name
        self.ch_set = set()
        self.dur = 0
        self.p_dict = dict()

        # Among given pulses, there may be several with negative offsets.
        #
        # If one just sequentially passes the them to insert(), it will shift
        # the T-origin. But the requested offsets for next pulses will not change,
        # thus next pulses will be place in unexpected shifted positions
        # (when passing several pulses at a time, the user thinks of the whole block
        # in a single frame and the offsets mean mutual position of pulses).
        #
        # To avoid this problem, below one checks all pulses, finds the largest
        # negative offset t_shift and just shifts all pulses by this amount before
        # calling insert(). In this case insert() does not perform any origin
        # shift.

        t_shift = 0
        for p_obj in p_obj_list:
            if p_obj.t0 < 0:
                t_shift = max(t_shift, abs(p_obj.t0))

        # Iterate through all given pulses and
        # insert them into the block
        for p_obj in p_obj_list:

            p_obj = copy.deepcopy(p_obj)
            p_obj.t0 += t_shift

            self.insert(p_obj=p_obj)

    def insert(self, p_obj, cflct_er=True):

        p_obj = copy.deepcopy(p_obj)
        ch = p_obj.ch

        # Sanity check: new pulse does not conflict with existing pulses
        if cflct_er and ch in self.ch_set:

            p_list = self.p_dict[ch]

            t0_list = np.array(
                [p_item.t0 for p_item in p_list]
            )
            idx = np.searchsorted(t0_list, p_obj.t0)

            if idx > 0:
                # Check for overlap with existing pulse to the left
                if not (p_list[idx-1].t0 + p_list[idx-1].dur) <= p_obj.t0:
                    raise ValueError(
                        'insert(): given pulse {} overlaps with existing pulse to the left'
                        ''.format(p_obj)
                    )

            if idx < len(p_list):
                # Check for overlap with existing pulse to the right
                if not (p_obj.t0 + p_obj.dur) <= p_list[idx].t0:
                    raise ValueError(
                        'insert(): given pulse {} overlaps with existing pulse to the right'
                        ''.format(p_obj)
                    )

        # Create a new entry for 'ch' if it is not yet registered
        if ch not in self.ch_set:
            self.p_dict[ch] = []
            self.ch_set.add(ch)

        # Add p_obj as a new entry in 'ch' pulse list
        self.p_dict[ch].append(p_obj)

        # T-order pulses within 'ch'
        self.p_dict[ch].sort(
            key=lambda p_item: p_item.t0
        )

        # Expand block edges if the new pulse sticks out:
        #   - beyond the end
        self.dur = max(self.dur, p_obj.t0 + p_obj.dur)
        #   - before the beginning
        if p_obj.t0 < 0:

            # shift every pulse to the right
            t_shift = abs(p_obj.t0)

            for ch_ in self.ch_set:
                for p_item in self.p_dict[ch_]:
                    p_item.t0 += t_shift

            # update duration
            self.dur += t_shift

    def join(self, p_obj, cflct_er=True, name=''):
        new_pb = copy.deepcopy(self)
        new_pb.name = name
        new_pb.insert(p_obj=p_obj, cflct_er=cflct_er)
        return new_pb
        # pass

    def insert_pb(self, pb_obj, t0=0, cflct_er=True):

        pb_obj = copy.deepcopy(pb_obj)

        # Sanity check: no overlap between blocks
        if cflct_er and (self.ch_set & pb_obj.ch_set):
            if t0 >= 0:
                if not self.dur <= t0:
                    raise ValueError(
                        'insert_pb(): blocks overlap and cannot be merged. (DEBUG: t0 > 0)'
                    )
            else:
                if not pb_obj.dur <= abs(t0):
                    raise ValueError(
                        'insert_pb(): blocks overlap and cannot be merged. (DEBUG: t0 < 0)'
                    )

        # Calculate duration
        if t0 >= 0:
            self.dur = max(self.dur, pb_obj.dur + t0)
        else:
            self.dur = max(abs(t0) + self.dur, pb_obj.dur)

        # Shift all elements of the right-most block
        if t0 >= 0:
            for ch in pb_obj.ch_set:
                for p_item in pb_obj.p_dict[ch]:
                    p_item.t0 += t0
        else:
            for ch in self.ch_set:
                for p_item in self.p_dict[ch]:
                    p_item.t0 += abs(t0)

        # Register new channels
        for ch in pb_obj.ch_set:
            if ch not in self.ch_set:
                self.ch_set.add(ch)
                self.p_dict[ch] = []

        # Add new pulses
        for ch in pb_obj.ch_set:
            self.p_dict[ch].extend(
                pb_obj.p_dict[ch]
            )

            if t0 < 0:
                # Pulses from pb_obj were added from the right
                # Sort pulses in T-order to move them to the left
                self.p_dict[ch].sort(
                    key=lambda pulse_item: pulse_item.t0
                )

        # pass

    def join_pb(self, pb_obj, t0=0, cflct_er=True, name=''):
        new_pb = copy.deepcopy(self)
        new_pb.name = name
        new_pb.insert_pb(
            pb_obj=pb_obj,
            t0=t0,
            cflct_er=cflct_er
        )
        return new_pb
        # pass

    def save(self):
        # TODO: implement
        pass

    @staticmethod
    def load():
        # TODO: implement
        pass

    def __str__(self):
        ret_str = 'PulseBlock "{}" \n' \
                  'ch_set = {} \n' \
                  'dur = {:.2e} \n' \
                  'p_dict: \n' \
                  ''.format(self.name, self.ch_set, self.dur)

        # TODO: each p_item on a new line
        for ch in self.ch_set:
            ch_str = '    {}: '.format(ch)
            for p_obj in self.p_dict[ch]:
                ch_str += '{{{:.2e}, {:.2e}, {}}}  '.format(p_obj.t0, p_obj.dur, str(p_obj))

            ret_str += ch_str
            ret_str += '\n'

        return ret_str


# def merge(*pb_items, name=''):
#
#     # Handle three different types of input:
#     #
#     # 1) just PulseBlock - the block to be added without t-offset
#     #
#     # 2) tuple(PulseBlock_instance, offset) - the block to be added
#     # with t-offset
#     #
#     # 3) dict('p_obj'=Pulse_instance, 'chnl'='chnl_name', 't'=offset)
#     # a single pulse to be wrapped into a PulseBlock and added with
#     # offset.
#     #
#     # Analyze each arg_item and sore result in pb_dict_list.
#
#     pb_dict_list = []
#
#     for arg_item in pb_items:
#         # 1) just PulseBlock - block without t-offset
#         if isinstance(arg_item, PulseBlock):
#
#             pb_dict_list.append(
#                 dict(
#                     pb_obj=arg_item,
#                     offset=0
#                 )
#             )
#
#         # 2) tuple(PulseBlock_instance, offset)
#         elif isinstance(arg_item, tuple):
#
#             # Check that PulseBlock is given first
#             if not isinstance(arg_item[0], PulseBlock):
#                 raise ValueError(
#                     'merge(): wrong parameter order in {}.\n'
#                     'To specify offset, pass a tuple (PulseBlock, offset)'
#                     ''.format(arg_item)
#                 )
#
#             pb_dict_list.append(
#                 dict(
#                     pb_obj=arg_item[0],
#                     offset=str_to_float(arg_item[1])
#                 )
#             )
#
#         # 3) dict('p_obj'=Pulse_instance, 'chnl'='chnl_name', 't'=offset)
#         # a single pulse to be wrapped into a PulseBlock
#         elif isinstance(arg_item, dict):
#
#             # Note: single-pulsed PulseBlock effectively ignores negative
#             # offset arg_item['t'].
#             # That is why one has to extract offset and apply it manually.
#             if 't' in arg_item.keys():
#                 temp_t = arg_item['t']
#                 temp_ar_item = copy.deepcopy(arg_item)
#                 temp_ar_item['t'] = 0
#             else:
#                 temp_t = 0
#                 temp_ar_item = arg_item
#
#             pb_dict_list.append(
#                 dict(
#                     pb_obj=PulseBlock(temp_ar_item),
#                     offset=temp_t
#                 )
#             )
#
#         # Unknown type of argument
#         else:
#             raise ValueError(
#                 'merge(): invalid argument {} was passed \n'
#                 'Arguments can be only be PulseBlock, tuple(PulseBlock, offset), '
#                 'or dict("chnl"=channel_name, "t"=offset, "p_obj"=pulse_object).'
#                 ''.format(arg_item)
#             )
#
#     # Find the largest negative offset t_shift
#     # to shift all blocks before calling _merge()
#     t_shift = 0
#     for pb_dict in pb_dict_list:
#         if pb_dict['offset'] < 0:
#             t_shift = max(
#                 t_shift,
#                 abs(pb_dict['offset'])
#             )
#
#     # Create blank of the new PulseBlock, which will be returned
#     new_pb = PulseBlock()
#
#     # Add all given pulse blocks
#     # (shifted offset is expected to be non-negative for each one)
#     for pb_dict in pb_dict_list:
#         new_pb = _merge(
#             pb1=new_pb,
#             pb2=pb_dict['pb_obj'],
#             offset=t_shift + pb_dict['offset']
#         )
#
#     new_pb.name = name
#     return new_pb
#     # pass
#
#
# def _merge(pb1, pb2, offset=0, name=''):
#
#     offset = str_to_float(offset)
#
#     # Create copies of both pulse blocks
#     # to avoid modifying passed instances
#     pb1 = copy.deepcopy(pb1)
#     pb2 = copy.deepcopy(pb2)
#
#     # Sanity checks
#     #   - non-negative offset is expected
#     if offset < 0:
#         raise ValueError(
#             '_merge(): only positive offset is allowed for this low-level method. \n'
#             'Use merge() for more generic types of input'
#         )
#
#     #   - if there is channel overlap, there can be no temporal overlap
#     if pb1.chnl_set & pb2.chnl_set:
#         if offset < pb1.dur:
#             raise ValueError(
#                 '_merge(): pulse blocks with both channel and temporal overlap cannot be merged: '
#                 'there are conflicting bins for common channels'
#             )
#
#     # Create a blank of the new pulse block
#     # which will be returned
#     new_pb = PulseBlock(name=name)
#
#     # Register all channels
#     new_pb.ch_set = pb1.chnl_set | pb2.chnl_set
#     for chnl in new_pb.ch_set:
#         new_pb.p_dict[chnl] = []
#
#     # Calculate duration
#     new_pb.dur = max(pb1.dur, offset + pb2.dur)
#
#     # Shift all pulses in pb2 by offset
#     for chnl in pb2.chnl_set:
#         for pulse_dict_item in pb2.pulse_dict[chnl]:
#             pulse_dict_item['t'] += offset
#
#     # Fill-in new_pb.p_dict
#     #   Since pulse items are T-ordered in pb1 an pb2
#     #   and pb2 goes after pb1 (or there is no channel overlap),
#     #   for every chanel one can simply add all pulses from pb1
#     #   and then add all pulses from pb2.
#
#     for chnl in pb1.chnl_set:
#         new_pb.p_dict[chnl].extend(
#             pb1.pulse_dict[chnl]
#         )
#
#     for chnl in pb2.chnl_set:
#         new_pb.p_dict[chnl].extend(
#             pb2.pulse_dict[chnl]
#         )
#
#     return new_pb