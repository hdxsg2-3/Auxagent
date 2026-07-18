from marshmallow import Schema, fields, validate

class CopywriterGenerateSchema(Schema):
    product_desc = fields.Str(required=True, validate=validate.Length(min=1))
    platform = fields.Str(required=True, validate=validate.OneOf(['amazon', 'ebay', 'aliexpress']))
    target_language = fields.Str(required=True, validate=validate.OneOf(['en', 'es', 'de', 'fr', 'zh']))

class CopywriterTranslateSchema(Schema):
    title = fields.Str(required=True)
    bullet_points = fields.List(fields.Str(), required=True)
    description = fields.Str(required=True)
    target_language = fields.Str(required=True, validate=validate.OneOf(['en', 'es', 'de', 'fr', 'zh']))

class AutoListingSchema(Schema):
    url = fields.Str(required=True, validate=validate.Length(min=10))

class ComplianceScanSchema(Schema):
    content = fields.Str(required=True, validate=validate.Length(min=1))
    images = fields.List(fields.Str())
    check_extreme_words = fields.Bool()
    check_copyright = fields.Bool()
    check_forbidden_words = fields.Bool()

class CustomerServiceProcessSchema(Schema):
    message = fields.Str(required=True)
    message_id = fields.Str(required=True)
    platform = fields.Str(required=True)

class LegalSearchSchema(Schema):
    query = fields.Str(required=True)
    regions = fields.List(fields.Str())

class LogisticsGenerateSchema(Schema):
    type = fields.Str(required=True)
    shipping_method = fields.Str(required=True)
    sender = fields.Dict(required=True)
    receiver = fields.Dict(required=True)
    items = fields.List(fields.Dict(), required=True)
    total_packages = fields.Int()
    total_weight = fields.Float()

class SettingsUpdateSchema(Schema):
    type = fields.Str(required=True)
    data = fields.Dict(required=True)

def validate_request(schema_class, data):
    schema = schema_class()
    errors = schema.validate(data)
    if errors:
        return {'valid': False, 'errors': errors}
    return {'valid': True, 'errors': None}
