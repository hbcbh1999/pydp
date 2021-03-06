"""
build in order to stay organized and to afford 'playing' with the algorithms implemented
helper module containing:
 a) random distributed data
 b) quality functions
 c) methods related to differential privacy notions
"""
import numpy as np
from collections import deque


def point_concept(p):
    """
    create a point concept function
    :param p: identity of point which identical points will be labeled by 1
    :return: point concept function that label point by 1 iff point == p
    """
    def concept(x):
        if x == p:
            return 1
        else:
            return 0
    return concept


def __make_point_data__(data_size, specify_spike):
    if specify_spike == -1:
        spike = np.random.randint(data_size, size=1)
    else:
        spike = specify_spike
    if spike > data_size:
        raise ValueError('ERR: spike index is bigger than the data length')
    point_data = [0]*data_size
    point_data[spike] = 1
    return point_data


def __make_threshold_data__(data_size, specify_threshold):
    if specify_threshold == -1:
        threshold = np.random.randint(data_size, size=1)[0]
    else:
        threshold = specify_threshold
    if threshold > data_size:
        raise ValueError('ERR: threshold index is bigger than the data length')
    threshold_data = [1]*threshold+[0]*(data_size-threshold)
    return threshold_data


def get_random_data(data_size, distribution_type='normal', pivot=0, specify_parameter=-1):
    """
    get a simple random data set
    :param data_size: number of elements
    :param distribution_type: specify the data type or remain empty to get a normal distributed one
    :return: random data set from a specific tpe
    """

    # TODO is this a good design??
    # lazy switch to get the desirable distribution
    data_switch = {
        'normal': lambda: np.random.normal(pivot, data_size / 6.0, data_size),
        'laplace': lambda: np.random.laplace(pivot, data_size / 100.0, data_size),
        'bimodal': lambda: np.concatenate([np.random.exponential(data_size * 0.07, data_size / 2),
                                   np.random.normal(data_size / 2, data_size / 10.0, data_size / 2)]),
        'uniform': lambda: np.random.uniform(pivot, data_size, data_size),
        'point': lambda: __make_point_data__(data_size, specify_parameter),  # POINT_d
        'threshold': lambda: __make_threshold_data__(data_size, specify_parameter),  # THRESH_d
        'splitted': lambda: np.array([pivot/3., pivot/3.*5] * (data_size / 2))
    }
    # if user call for unknown data-type return a normal distributed one
    return data_switch.get(distribution_type, data_switch['normal'])()


def get_labeled_sample(data, sample_size):
    """
    get a rando labled sample from a labeled data set
    :param data: list of values
    :param sample_size: the number of samples to return
    :return: list of two lists -
    one containing the indexes sampled
    and the second containing the values in those indexes
    """
    data_size = len(data)
    sampled_data_x = sorted(np.random.choice(data_size, sample_size))
    sampled_data_y = [data[sampled_data_x[i]] for i in xrange(len(sampled_data_x))]
    sampled_data = [sampled_data_x, sampled_data_y]
    return sampled_data


def make_neighbour_set(data, label_type='float'):
    """
    create new data set that differ from the data exactly in one element
    used to check privacy under the classic differential privacy definition
    :param data: the original data set
    :return: data set that differ from the data exactly in one element
    """
    target_index = np.random.randint(len(data))

    # remove random element
    neighbor_data = np.delete(data, target_index)

    # TODO adding necessary?
    # add random element
    random_element = {
        'float': np.random.uniform(min(data), max(data)),
        'int': np.random.randint(min(data), max(data)),
        'binary': np.random.randint(2),
    }
    neighbor_data = np.insert(neighbor_data, target_index, random_element.get(label_type))
    return neighbor_data


# TODO needed?
def databases_distance(data_1, data_2):
    return sum(data_1 != data_2)


def __build_intervals_set__(data_base, interval_length, range_start, range_max, shift=False):
    # TODO maybe move this method outside of the module
    # TODO remove non-negative assumption dependence
    # assuming all the data is non-negative
    data_que = deque(sorted(data_base))
    list_of_intervals = []
    # data_next = -1
    data_next = data_que.popleft()

    while data_next < range_start:
        data_next = data_que.popleft()

    while len(data_que) > 0 and data_next <= range_max:
        next_relevant_interval_start = (int(data_next - shift * interval_length/2) / interval_length) \
                                       * interval_length + shift*interval_length/2
        # TODO remove redundant variable
        next_relevant_interval = next_relevant_interval_start
        list_of_intervals.append(next_relevant_interval)
        while data_next < next_relevant_interval + interval_length and len(data_que) > 0:
            data_next = data_que.popleft()

    return list_of_intervals


def __old_build_intervals_set__(data_base, interval_length, range_start, range_max, shift=False):
    # TODO move this method outside of the module
    # TODO remove non-negative assumption dependence
    # assuming all the data is non-negative
    data_que = deque(sorted(data_base))
    list_of_intervals = []
    # data_next = -1
    data_next = data_que.popleft()

    while data_next < range_start:
        data_next = data_que.popleft()

    while len(data_que) > 0 and data_next <= range_max:
        next_relevant_interval_start = (int(data_next - shift * interval_length/2) / interval_length) \
                                       * interval_length + shift*interval_length/2
        next_relevant_interval = (next_relevant_interval_start, next_relevant_interval_start + interval_length)
        list_of_intervals.append(next_relevant_interval)
        while data_next < next_relevant_interval[1] and len(data_que) > 0:
            data_next = data_que.popleft()

    return list_of_intervals

