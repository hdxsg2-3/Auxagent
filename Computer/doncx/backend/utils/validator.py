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
    content = fields.Str(allow_none=True, load_default='')
    images = fields.List(fields.Raw(), load_default=list)
    check_extreme_words = fields.Bool(load_default=True)
    check_copyright = fields.Bool(load_default=True)
    check_forbidden_words = fields.Bool(load_default=True)

class ImageAnalyzeSchema(Schema):
    name = fields.Str(required=True)
    base64 = fields.Str(required=True, validate=validate.Length(min=1))

class CustomerServiceProcessSchema(Schema):
    message = fields.Str(required=True)
    message_id = fields.Raw()
    platform = fields.Str(required=True)
    buyer_id = fields.Str()

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

class LogisticsStatusUpdateSchema(Schema):
    status = fields.Str(required=True)
    tracking_number = fields.Str()
    carrier = fields.Str()

class LogisticsTrackingAddSchema(Schema):
    status = fields.Str(required=True)
    location = fields.Str()
    description = fields.Str()

class SettingsUpdateSchema(Schema):
    type = fields.Str(required=True)
    data = fields.Dict(required=True)


class ShopCreateSchema(Schema):
    platform = fields.Str(required=True, validate=validate.OneOf(['amazon', 'temu', 'ebay', 'local-shop']))
    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    region = fields.Str()
    credentials = fields.Dict()
    mock = fields.Bool()
    status = fields.Str(load_default='active')


class ShopUpdateSchema(Schema):
    platform = fields.Str(validate=validate.OneOf(['amazon', 'temu', 'ebay', 'local-shop']))
    name = fields.Str(validate=validate.Length(min=1, max=100))
    region = fields.Str()
    credentials = fields.Dict()
    status = fields.Str()
    mock = fields.Bool()


class ShopPublishSchema(Schema):
    sku = fields.Str(required=True)
    title = fields.Str(required=True)
    bullet_points = fields.List(fields.Str())
    description = fields.Str()
    price = fields.Float()
    stock = fields.Int()
    product_type = fields.Str()
    images = fields.List(fields.Str())
    category_id = fields.Str()


class ShopSendMessageSchema(Schema):
    order_id = fields.Str(required=True)
    buyer_id = fields.Str()
    text = fields.Str(required=True)


def validate_request(schema_class, data):
    schema = schema_class()
    errors = schema.validate(data)
    if errors:
        return {'valid': False, 'errors': errors}
    return {'valid': True, 'errors': None}
