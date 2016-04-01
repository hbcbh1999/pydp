import numpy as np
from basicdp import choosing_mechanism_big, above_threshold
from collections import Counter
from jl import johnson_lindenstrauss_transform_init as jl_init
from functools import partial
from scipy.spatial import distance


def __box_containing_point__(point, partition, dimension, side_length):
    return tuple(np.floor((point[i]-partition[i]) / side_length) for i in xrange(dimension))


def __interval_containing_point__(point, side_length):
    return np.floor(point / side_length)


def find(data, number_of_points, data_dimension, radius, points_in_ball,
         failure, approximation, eps, delta, shrink=False):
    # step 1
    print "step 1"
    if shrink:
        new_dimension = int(46 * number_of_points * np.log2(2 * number_of_points / failure))
    else:
        new_dimension = data_dimension
    box_side_length = 300 * radius

    # step 2
    print "step 2"
    if shrink:
        transform = jl_init(data_dimension, new_dimension)
        projected_data = transform(data)
    else:
        def transform(x): return x
        projected_data = data
    threshold = points_in_ball - 100 * np.log2(2 * number_of_points / failure) / eps
    print "the threshold is: %f" % threshold
    above_thresh = above_threshold(projected_data, threshold, eps/4.0)

    # step 3
    print "step 3"
    boxes_shift = []  # just to make sure the list is defined in step 7
    found_max = False
    tries = 2 * number_of_points * int(np.log2(1 / failure)) / failure
    print "no. of tries: %d" % tries
    while not found_max and tries > 0:
        boxes_shift = np.random.uniform(0, box_side_length, new_dimension)

        # step 5
        print "step 5"

        def partition_quality(data_base):
            # TODO seems like I am ignoring 0-quality elements. Need fix?
            boxes = (__box_containing_point__(p, boxes_shift, new_dimension, box_side_length) for p in data_base)
            c = Counter(boxes)
            return c[max(c, key=c.get)]

        print "biggest cluster in a single box: %d" % partition_quality(projected_data)
        find_best_box = above_thresh(partition_quality)
        if find_best_box == 'up':
            found_max = True
        else:  # find_best_box == 'bottom'
            tries -= 1

    # step 6
    print "step 6"
    if not found_max:
        return -1

    # step 7
    print "step 7"
    box_containing_point_our_case = partial(__box_containing_point__, partition=boxes_shift, dimension=new_dimension,
                            side_length=box_side_length)
    boxes = (box_containing_point_our_case(point) for point in data)
    boxes_quality = Counter(boxes)

    # we add data_base to the signature to match the requirements of choosing_mechanism
    def box_quality(data_base, box):
        return boxes_quality[box]

    boxes_set = list(set(box_containing_point_our_case(p) for p in data))
    # TODO what is the growth bound?
    best_box = choosing_mechanism_big(projected_data, boxes_set, box_quality, 1,
                                          approximation, failure, eps/4.0, delta/4.0)
    # the first reshape is due to the signature of the transform method
    # the second reshape returns the box to the original structure so we can compare to the best_box
    points_in_best_box = [p for p in data
                          if box_containing_point_our_case(transform(p.reshape(1, data_dimension)).reshape(data_dimension,)) == best_box]

    print "step 8"
    interval_length = 450 * radius * np.sqrt(new_dimension)
    center_box = []
    for axis in xrange(data_dimension):
        axis_projection = np.array([__interval_containing_point__(d[axis], interval_length)
                                    for d in points_in_best_box])
        axis_counter = Counter(axis_projection)

        def interval_quality(data_base, interval_index):
            return axis_counter[interval_index]

        eps_tag = eps / np.sqrt(data_dimension * np.log(8/delta)) / 10.0
        delta_tag = delta / data_dimension / 8.0
        # TODO what is the growth bound?
        # TODO what is the failure and approximation parameter
        best_interval = choosing_mechanism_big(projected_data, axis_projection, interval_quality,
                                                       1, approximation, failure, eps_tag, delta_tag)

        extended_interval = (best_interval-1 * interval_length, (best_interval+2) * interval_length)
        center_box.append(extended_interval)
    print "step 9"
    center_of_chosen_box = [(i[1]-i[0])/2. for i in center_box]
    chosen_ball = [p for p in data if distance.euclidean(center_of_chosen_box, p) <= interval_length*3]
    # TODO step 10
    return best_box, box_quality(data, best_box), center_box, chosen_ball

