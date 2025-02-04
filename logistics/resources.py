from import_export import fields, resources
from import_export.widgets import IntegerWidget

from logistics.models import Claim, EquipmentData


class EquipmentDataResource(resources.ModelResource):
    class Meta:
        model = EquipmentData
        fields = ("brand", "model", "width", "height", "depth", "weight")
        import_id_fields = ("brand", "model")


class ClaimExportResource(resources.ModelResource):
    amount = fields.Field(attribute="amount", widget=IntegerWidget())
    type = fields.Field(attribute="offered_item__get_type_display")
    brand = fields.Field(attribute="offered_item__brand")
    model = fields.Field(attribute="offered_item__model")

    shipment = fields.Field(attribute="shipment")

    donor_first_name = fields.Field(attribute="offered_item__offer__contact__first_name")
    donor_last_name = fields.Field(attribute="offered_item__offer__contact__last_name")
    donor_email = fields.Field(attribute="offered_item__offer__contact__email")
    donor_organisation = fields.Field(attribute="offered_item__offer__contact__organisation__name")

    requester_first_name = fields.Field(attribute="requested_item__request__contact__first_name")
    requester_last_name = fields.Field(attribute="requested_item__request__contact__last_name")
    requester_email = fields.Field(attribute="requested_item__request__contact__email")
    requester_organisation = fields.Field(attribute="requested_item__request__contact__organisation__name")

    class Meta:
        model = Claim
        fields = (
            "amount",
            "type",
            "brand",
            "model",
            "shipment",
            "donor_first_name",
            "donor_last_name",
            "donor_email",
            "donor_organisation",
            "requester_first_name",
            "requester_last_name",
            "requester_email",
            "requester_organisation",
        )
