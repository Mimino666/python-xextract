def flatten(x):
    '''flatten(sequence) -> list

    Returns a single, flat list which contains all elements retrieved
    from the sequence and all recursively contained sub-sequences
    (iterables).
    '''
    result = []
    for el in x:
        if hasattr(el, '__iter__'):
            result.extend(flatten(el))
        else:
            result.append(el)
    return result
