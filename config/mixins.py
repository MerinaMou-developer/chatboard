class OrgScopedMixin:
    """
    Each view that cares about org should implement how to extract org_id
    from path params or request data. Default returns None.
    """
    def org_id_from_request(self, request):
        return None
