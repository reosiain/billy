class StaleNewsException(Exception):
    pass


class ShallowSentimentError(Exception):
    """Predicted neutral sentiment"""

    pass


class NoTargetError(Exception):
    """No ticker for the news"""

    pass


class MultiTargetError(Exception):
    """Multiple companies mentioned in the article ticker for the news"""

    pass


class ContextError(Exception):
    """Trade with similar context is already open"""

    pass

class ConstructionError(Exception):
    """Unable to construct Trade due to missing parameters"""

    pass

