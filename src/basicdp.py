import numpy as np
from random import choice
import gmpy2


def noisy_max(data, domain, quality_function, eps, bulk=False):
    """Noisy-Max Mechanism
    noisy_max ( data , domain, quality function , privacy parameter )
    :param data: list or array of values
    :param domain: list of possible results
    :param quality_function: function which get as input the data and a domain element and 'qualifies' it
    :param eps: privacy  parameter
    :param bulk: in case that we can reduce run-time by evaluating the quality of the whole domain in bulk,
    the procedure will be given a 'bulk' quality function. meaning that instead of one domain element the
    quality function get the whole domain as input
    :return: an element of domain with approximately maximum value of quality function
    """

    # compute q(X,i) for all the elements in D
    if bulk:
        qualified_domain = quality_function(data, domain)
    else:
        qualified_domain = [quality_function(data, i) for i in domain]
    # add Lap(1/eps) noise for each element in qualified_domain
    noisy = [q + np.random.laplace(0, 1 / eps, 1) for q in qualified_domain]
    # return element with maximum noisy q(X,i)
    return domain[noisy.index(max(noisy))]


def exponential_mechanism(data, domain, quality_function, eps, bulk=False, for_sparse=False):
    """Exponential Mechanism
    exponential_mechanism ( data , domain , quality function , privacy parameter )
    :param data: list or array of values
    :param domain: list of possible results
    :param quality_function: function which get as input the data and a domain element and 'qualifies' it
    :param eps: privacy parameter
    :param bulk: in case that we can reduce run-time by evaluating the quality of the whole domain in bulk,
    the procedure will be given a 'bulk' quality function. meaning that instead of one domain element the
    quality function get the whole domain as input
    :param for_sparse: in cases that the domain is a very spared one, namely a big percent of the domain has quality 0,
    there is a special procedure called sparse_domain. That procedure needs, beside that result from the given
    mechanism, the total weight of the domain whose quality is more than 0. If that is the case Exponential-Mechanism
    will return also the P DF before the normalization.
    :return: an element of domain with approximately maximum value of quality function
    """

    # calculate a list of probabilities for each element in the domain D
    # probability of element d in domain proportional to exp(eps*quality(data,d)/2)
    if bulk:
        qualified_domain = quality_function(data, domain)
        domain_pdf = [np.exp(eps * q / 2) for q in qualified_domain]
    else:
        domain_pdf = [np.exp(eps * quality_function(data, d) / 2) for d in domain]
    total_value = float(sum(domain_pdf))
    domain_pdf = [d / total_value for d in domain_pdf]
    normalizer = sum(domain_pdf)
    # for debugging and other reasons: check that domain_cdf indeed defines a distribution
    # use the uniform distribution (from 0 to 1) to pick an elements by the CDF
    if abs(normalizer - 1) > 0.001:
        raise ValueError('ERR: exponential_mechanism, sum(domain_pdf) != 1.')

    # accumulate elements to get the CDF of the exponential distribution
    domain_cdf = np.cumsum(domain_pdf).tolist()
    # pick a uniformly random value on the CDF
    pick = np.random.uniform()

    # return the index corresponding to the pick
    # take the min between the index and  len(D)-1 to prevent returning index out of bound
    result = domain[min(np.searchsorted(domain_cdf, pick), len(domain)-1)]
    # in exponential_mechanism_sparse we need also the total_sum value
    if for_sparse:
        return result, total_value
    return result


def __pick_out_of_sub_group__(group, subgroup):
    """
    Pick at random an element from subgroup
    build for the use of the sparse_domain procedure
    :param group: The whole group of values
    :param subgroup: THe sub-group of values to pick an element from
    :return: random element of the group which is contained in the subgroup
    """
    pick = 0
    good_pick = False
    while not good_pick:
        pick = choice(group)
        if pick not in subgroup:
            good_pick = True
    return pick


# TODO decide - this more generic version or a more specific one
def sparse_domain(mechanism, data, domain, positive_value, quality_function, eps, delta=0, bulk=False):
    """
    Wrapper for compatible mechanisms. In the case that the non-zero-quality part of the input domain is
    relatively small. The wrapper uses that information to get an improvement in run-time.
    :param mechanism: the private mechanism to be executed (such as the exponential-mechanism etc.)
    :param data: list or array of values
    :param domain: list of possible results
    :param positive_value: list of possible results with positive quality
    :param quality_function: function which get as input the data and a domain element and 'qualifies' it
    :param eps: privacy parameter
    :param delta: privacy parameter
    :param bulk: in case that we can reduce run-time by evaluating the quality of the whole domain in bulk,
    the procedure will be given a 'bulk' quality function. meaning that instead of one domain element the
    quality function get the whole domain as input
    :return: the result of the mechanism on the given input
    """
    if delta == 0:
        r1, positives_size = mechanism(data, positive_value, quality_function, eps, bulk, for_sparse=True)
    else:
        r1, positives_size = mechanism(data, positive_value, quality_function, eps, delta, bulk, for_sparse=True)
    r2 = __pick_out_of_sub_group__(domain, positive_value)
    zero_size = len(domain)-len(positive_value)
    p = float(positives_size/(zero_size + positives_size))
    coin = np.random.binomial(1, p)
    if coin:
        return r1
    else:
        return r2


def a_dist(data, domain, quality_function, eps, delta, bulk=False, for_sparse=False):
    """A_dist algorithm
    :param data: list or array of values
    :param domain: list of possible results
    :param quality_function: sensitivity-1 quality function
    :param eps: privacy parameter
    :param delta: privacy parameter
    :param bulk: in case that we can reduce run-time by evaluating the quality of the whole domain in bulk,
    the procedure will be given a 'bulk' quality function. meaning that instead of one domain element the
    quality function get the whole domain as input
    :param for_sparse: in cases that the domain is a very spared one, namely a big percent of the domain has quality 0,
    there is a special procedure called sparse_domain. That procedure needs, beside that result from the given
    mechanism, the total weight of the domain whose quality is more than 0. If that is the case A-dist
    will return also the total quality weight input domain.
    :return: an element of domain with maximum value of quality function or 'bottom'
    """

    # compute q(X,i) for all the elements in D
    if bulk:
        qualified_domain = quality_function(data, domain)
    else:
        qualified_domain = [quality_function(data, i) for i in domain]
    total_value = float(sum(qualified_domain))
    h1_score = max(qualified_domain)
    h1 = domain[qualified_domain.index(h1_score)]  # h1 is domain element with highest quality
    qualified_domain.remove(h1_score)
    domain.remove(h1)
    h2_score = max(qualified_domain)
    # h2 = domain[qualified_domain.index(h2_score)]  # h2 is domain element with second-highest quality
    noisy_gap = h1_score - h2_score + np.random.laplace(0, 1 / eps, 1)
    if noisy_gap < np.log(1/delta)/eps:
        return 'bottom'
    elif for_sparse:
        return h1, total_value
    else:
        return h1


def above_threshold_on_queries(data, queries, threshold, eps):
    """
    above_threshold algorithm - privacy preserving algorithm that given a list of sensitivity-1 queries
    tests if their evaluation over the given data exceeds the threshold
    :param data: list or array of values
    :param queries: list of queries
    :param threshold: fixed threshold
    :param eps: privacy parameter
    :return: list of answers to the queries until the first time we get answer above the threshold
    """

    initialized_threshold = above_threshold(data, threshold, eps)
    answers = []
    for q in queries:
        query_result = initialized_threshold(q)
        answers.append(query_result)
        if query_result == 'up':
            break
    return answers


def above_threshold(data, threshold, eps):
    """
    above_threshold algorithm - privacy preserving algorithm that given a stream of sensitivity-1 queries
    tests if their evaluation over the given data exceeds the threshold
    :param data: list or array of values
    :param threshold: fixed threshold
    :param eps: privacy parameter
    :return: threshold_instance that get queries as input
    and for every given query evaluate the private above-threshold test
    """

    noisy_threshold = threshold + np.random.laplace(0, 2 / eps, 1)

    def threshold_instance(query):
        noise = np.random.laplace(0, 4 / eps, 1)
        if query(data) + noise >= noisy_threshold:
            return 'up'
        else:
            return 'bottom'
    return threshold_instance


def choosing_mechanism(data, solution_set, quality_function, alpha, eps,
                       delta=0, beta=0, growth_bound=1, check_bound=True):
    """
    Choosing Mechanism for solving bounded-growth choice problems
    :param data: list or array of values
    :param solution_set: list of possible results
    :param quality_function: k-bounded-growth quality function
    :param alpha: approximation parameter
    :param eps: privacy parameters
    :param check_bound: test if the parameters satisfy the lower bound for privacy guarantee
    :param delta: privacy parameters. only needed if check_bound=True
    :param beta: chances that the procedure will fail to return an answer. only needed if check_bound=True
    :param growth_bound: bounding parameter on the growth of the quality function. only needed if check_bound=True
    :return: an element of domain with approximately maximum value of quality function
    """
    data_size = len(data)
    if check_bound:
        if data_size < 16 * np.log(16 * growth_bound / alpha / beta / eps / delta) / alpha / eps:
            raise ValueError("privacy problem - data size too small")
    best_quality = max(quality_function(data, f) for f in solution_set) + np.random.laplace(0, 4 / eps, 1)
    if best_quality < alpha * data_size / 2.0:
        return 'bottom'
    smaller_solution_set = [f for f in solution_set if quality_function(data, f) >= 1]
    return exponential_mechanism(data, smaller_solution_set, quality_function, eps)


# TODO i think those two 'big' versions should be merged into the normal ones somehow
def exponential_mechanism_big(data, domain, quality_function, eps, bulk=False, for_sparse=False):
    """Exponential Mechanism that can deal with very large or very small qualities
    exponential_mechanism ( data , domain , quality function , privacy parameter )
    :param data: list or array of values
    :param domain: list of possible results
    :param quality_function: function which get as input the data and a domain element and 'qualifies' it
    :param eps: privacy parameter
    :param bulk: in case that we can reduce run-time by evaluating the quality of the whole domain in bulk,
    the procedure will be given a 'bulk' quality function. meaning that instead of one domain element the
    quality function get the whole domain as input
    :param for_sparse: in cases that the domain is a very spared one, namely a big percent of the domain has quality 0,
    there is a special procedure called sparse_domain. That procedure needs, beside that result from the given
    mechanism, the total weight of the domain whose quality is more than 0. If that is the case Exponential-Mechanism
    will return also the P DF before the normalization.
    :return: an element of domain with approximately maximum value of quality function
    """

    # calculate a list of probabilities for each element in the domain D
    # probability of element d in domain proportional to exp(eps*quality(data,d)/2)
    if bulk:
        qualified_domain = quality_function(data, domain)
        domain_pdf = [gmpy2.exp(eps * q / 2) for q in qualified_domain]
    else:
        domain_pdf = [gmpy2.exp(eps * quality_function(data, d) / 2) for d in domain]
    total_value = sum(domain_pdf)
    domain_pdf = [d / total_value for d in domain_pdf]
    normalizer = sum(domain_pdf)
    # for debugging and other reasons: check that domain_cdf indeed defines a distribution
    # use the uniform distribution (from 0 to 1) to pick an elements by the CDF
    if abs(normalizer - 1) > 0.001:
        raise ValueError('ERR: exponential_mechanism, sum(domain_pdf) != 1.')

    # accumulate elements to get the CDF of the exponential distribution
    domain_cdf = np.cumsum(domain_pdf).tolist()
    # pick a uniformly random value on the CDF
    pick = np.random.uniform()

    # return the index corresponding to the pick
    # take the min between the index and  len(D)-1 to prevent returning index out of bound
    result = domain[min(np.searchsorted(domain_cdf, pick), len(domain)-1)]
    # in exponential_mechanism_sparse we need also the total_sum value
    if for_sparse:
        return result, total_value
    return result


def choosing_mechanism_big(data, solution_set, quality_function, alpha, eps,
                       delta=0, beta=0, growth_bound=1, check_bound=True):
    """
    Choosing Mechanism for solving bounded-growth choice problems
    that can deal with very large or very small qualities
    :param data: list or array of values
    :param solution_set: list of possible results
    :param quality_function: k-bounded-growth quality function
    :param alpha: approximation parameter
    :param eps: privacy parameters
    :param check_bound: test if the parameters satisfy the lower bound for privacy guarantee
    :param delta: privacy parameters. only needed if check_bound=True
    :param beta: chances that the procedure will fail to return an answer. only needed if check_bound=True
    :param growth_bound: bounding parameter on the growth of the quality function. only needed if check_bound=True
    :return: an element of domain with approximately maximum value of quality function

    """
    data_size = len(data)
    if check_bound:
        if data_size < 16 * np.log(16 * growth_bound / alpha / beta / eps / delta) / alpha / eps:
            raise ValueError("privacy problem - data size too small")
    if not len(solution_set):
        raise ValueError('domain is empty')
    best_quality = max(quality_function(data, f) for f in solution_set) + np.random.laplace(0, 4 / eps, 1)
    if best_quality < alpha * data_size / 2.0:
        return 'bottom'
        # return choice(solution_set)
    smaller_solution_set = [f for f in solution_set if quality_function(data, f) >= 1]
    return exponential_mechanism_big(data, smaller_solution_set, quality_function, eps)


def noisy_avg(vector_multi_set, predicate, dim, eps, delta):
    """
    Based on "Appendix A - Noisy average of vectors in R^d" from "Locating a Small Cluster Privately" by
     Kobbi Nissim, Uri Stemmer, and Salil Vadhan. PODS 2016.
    Given Given a multiset of vectors in R^d, obtain privately their approximate average
     with respect to soe given predicate
    :param vector_multi_set: list of tuples
    :param predicate: binary function from vectors in R^dim to {0,1}
    :param dim: the dimension of the space which the vectors are taken from
    :param eps: privacy parameter
    :param delta: privacy parameter
    :return: private approximate average of the vectors with respect to soe given predicate
    """
    delta_g = max(np.linalg.norm(v) for v in vector_multi_set if predicate(v))
    size_of_vectrs_set = sum(1 for v in set(vector_multi_set) if predicate(v))
    m = size_of_vectrs_set + np.random.laplace(0, 2/eps, 1) - 2*np.log(2/delta)/eps
    if m <= 0:
        return 'bottom'
    sigma = 8 * delta_g * np.sqrt(2*np.log(8/delta)) / eps / m
    r = np.random.normal(0, sigma, dim)
    return np.sum([list(v) for v in vector_multi_set if predicate(v)], axis=0) / float(size_of_vectrs_set) + r
