class SchemaService:
    @staticmethod
    def to_internal_schema(raw: dict):
        # TODO: convert to internal schema
        return {"status": "schema_stub", "raw": raw}

    @staticmethod
    def to_output_schema(internal: dict):
        # TODO: convert to frontend schema
        return {"status": "output_schema_stub", "internal": internal}
