from django.contrib import admin
from django.db.models import F, Sum
from django.db.models.functions import Coalesce
from django.forms.models import BaseInlineFormSet
from django.http import HttpRequest, HttpResponseRedirect
from django.shortcuts import render
from django.templatetags.static import static
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from import_export.admin import ExportActionModelAdmin, ImportExportActionModelAdmin
from logistics.filters import UsedChoicesFieldListFilter
from logistics.forms import AssignToShipmentForm
from logistics.models import EquipmentData, Item, Location, Shipment, ShipmentItem
from logistics.resources import EquipmentDataResource

static_import_icon = static("img/import.png")
static_export_icon = static("img/export.png")


@admin.register(EquipmentData)
class EquipmentDataAdmin(ImportExportActionModelAdmin):
    list_display = ("brand", "model", "admin_weight", "admin_size")
    ordering = ("brand", "model")
    resource_class = EquipmentDataResource

    @admin.display(description=_("weight"), ordering="weight")
    def admin_weight(self, item: EquipmentData):
        if item.weight:
            return f"{item.weight} kg"
        else:
            return "-"

    @admin.display(description=_("size (W*H*D)"), ordering="width,height,depth")
    def admin_size(self, item: EquipmentData):
        if item.width or item.height or item.depth:
            return f'{item.width or "?"} x {item.height or "?"} x {item.depth or "?"} cm'
        else:
            return "-"


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "country",
        "admin_email",
        "admin_phone",
        "type",
        "managed_by",
    )
    list_filter = (
        ("country", UsedChoicesFieldListFilter),
        "type",
    )
    ordering = ("name",)

    @admin.display(description=_("contact email"), ordering="email")
    def admin_email(self, location: Location):
        if not location.email:
            return None

        return format_html('<a href="mailto:{email}">{email}</a>', email=location.email)

    @admin.display(description=_("contact phone"), ordering="phone")
    def admin_phone(self, location: Location):
        if not location.phone:
            return None

        return format_html('<a href="tel:{phone}">{phone}</a>', phone=location.phone)


class ShipmentItemInlineAdmin(admin.TabularInline):
    model = ShipmentItem
    extra = 0
    max_num = 0
    readonly_fields = (
        "offered_item",
        "amount",
        "last_location",
    )
    exclude = ("parent_shipment_item",)

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related("shipment")
        return qs


@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = ("name", "shipment_date", "delivery_date", "from_location", "to_location", "is_delivered", "notes")
    list_filter = ("is_delivered", "from_location", "to_location", "shipment_date", "delivery_date")
    date_hierarchy = "delivery_date"
    ordering = ("delivery_date",)
    search_fields = (
        "name",
        "to_location__name",
        "to_location__city",
        "to_location__country",
        "from_location__name",
        "from_location__city",
        "from_location__country",
    )

    inlines = (ShipmentItemInlineAdmin,)


@admin.register(ShipmentItem)
class ShipmentItemAdmin(ExportActionModelAdmin):
    list_display = (
        "offered_item",
        "amount",
        "shipment",
        "last_location",
        "is_delivered",
    )
    list_filter = (
        "last_location",
        "shipment",
        "shipment__is_delivered",
        (
            "offered_item__offer__contact__organisation",
            admin.RelatedOnlyFieldListFilter,
        ),
    )
    search_fields = (
        "offered_item__brand",
        "offered_item__model",
        "offered_item__offer__contact__organisation__name",
        "last_location",
    )
    autocomplete_fields = (
        "offered_item",
        "parent_shipment_item",
    )
    ordering = ("-created_at",)

    # TODO
    # resource_class = ShipmentItemExportResource

    def get_queryset(self, request: HttpRequest):
        qs = (
            super()
            .get_queryset(request)
            .select_related(
                "shipment",
                "offered_item__offer__contact__organisation",
                "offered_item",
            )
            .prefetch_related(
                "offered_item__requested_items__request__contact__organisation",
            )
        )
        return qs

    @admin.display(description=_("is delivered"), boolean=True)
    def is_delivered(self, item: ShipmentItem):
        return item.shipment and item.shipment.is_delivered


class ShipmentItemHistoryFormSet(BaseInlineFormSet):

    ordering = ("when",)

    def get_queryset(self):
        qs = ShipmentItem.objects.filter(offered_item=self.instance.offered_item).order_by("-when", "-created_at")
        return qs


class ShipmentItemHistoryInlineAdmin(admin.TabularInline):
    model = ShipmentItem
    verbose_name = _("Shipment History of Item")
    verbose_name_plural = _("Shipment History of Items")
    extra = 0
    max_num = 0
    formset = ShipmentItemHistoryFormSet
    can_delete = False
    readonly_fields = (
        "offered_item",
        "amount",
        "last_location",
        "shipment",
        "when",
    )
    # exclude = ("parent_shipment_item",)


@admin.register(Item)
class ItemAdmin(ShipmentItemAdmin):
    list_display = (
        "offered_item",
        "available",
        "amount",
        "last_location",
        "shipment",
        "is_delivered",
        "parent_shipment_item",
    )
    list_filter = (
        "last_location",
        "shipment",
        "shipment__is_delivered",
        (
            "offered_item__offer__contact__organisation",
            admin.RelatedOnlyFieldListFilter,
        ),
    )
    search_fields = (
        "offered_item__brand",
        "offered_item__model",
        "offered_item__offer__contact__organisation__name",
        "last_location",
    )
    ordering = ("-created_at",)
    actions = ("assign_to_shipment",)

    inlines = (ShipmentItemHistoryInlineAdmin,)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = (
            qs.annotate(sent=Coalesce(Sum("sent_items__amount"), 0))
            .prefetch_related("sent_items")
            .annotate(available=F("amount") - F("sent"))
            .filter(available__gt=0)
        )
        return qs

    @admin.action(description=_("Assign to shipment"))
    def assign_to_shipment(self, request, queryset):

        if "apply" in request.POST:
            shipment = Shipment.objects.get(id=request.POST["shipment"])
            amount_list = request.POST.getlist("amount")
            for index, item in enumerate(queryset):
                amount = amount_list[index]
                ShipmentItem.objects.create(
                    shipment=shipment,
                    offered_item=item.offered_item,
                    amount=amount,
                    last_location=shipment.from_location,
                    parent_shipment_item_id=item.id,
                )

            return HttpResponseRedirect(request.get_full_path())

        errors = []
        form = None
        if len(set(queryset.values_list("last_location", flat=True))) > 1:
            errors.append(_("Choosen items are in different locations."))
        if queryset.filter(shipment__is_delivered=False).exists():
            errors.append(_("Some of items are not delivered yet or attached to another shipment."))
        if not errors:
            shipment_queryset = Shipment.objects.filter(
                from_location=queryset.first().last_location,
            )
            form = AssignToShipmentForm(initial=dict(shipment_queryset=shipment_queryset))
        return render(
            request,
            "admin/assign_to_shipment.html",
            context={"items": queryset, "errors": errors, "form": form, "adjustable_amount": True},
        )

    @admin.display(description=_("available"))
    def available(self, item: Item):
        return item.available
