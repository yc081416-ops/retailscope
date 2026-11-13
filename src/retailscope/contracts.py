"""Olist source CSV contracts. Raw PostgreSQL layer preserves all source values as TEXT.

The misspelled 'lenght' column names are intentional: they match Olist's original headers.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class SourceSpec:
    file_name: str
    table_name: str
    columns: tuple[str, ...]
    unique_key: tuple[str, ...] = ()
    numeric_columns: tuple[str, ...] = ()
    date_columns: tuple[str, ...] = ()


SOURCES: tuple[SourceSpec, ...] = (
    SourceSpec(
        "olist_customers_dataset.csv", "customers",
        ("customer_id", "customer_unique_id", "customer_zip_code_prefix", "customer_city", "customer_state"),
        ("customer_id",),
    ),
    SourceSpec(
        "olist_geolocation_dataset.csv", "geolocation",
        ("geolocation_zip_code_prefix", "geolocation_lat", "geolocation_lng", "geolocation_city", "geolocation_state"),
        numeric_columns=("geolocation_lat", "geolocation_lng"),
    ),
    SourceSpec(
        "olist_order_items_dataset.csv", "order_items",
        ("order_id", "order_item_id", "product_id", "seller_id", "shipping_limit_date", "price", "freight_value"),
        ("order_id", "order_item_id"),
        ("order_item_id", "price", "freight_value"),
        ("shipping_limit_date",),
    ),
    SourceSpec(
        "olist_order_payments_dataset.csv", "order_payments",
        ("order_id", "payment_sequential", "payment_type", "payment_installments", "payment_value"),
        ("order_id", "payment_sequential"),
        ("payment_sequential", "payment_installments", "payment_value"),
    ),
    SourceSpec(
        "olist_order_reviews_dataset.csv", "order_reviews",
        ("review_id", "order_id", "review_score", "review_comment_title", "review_comment_message", "review_creation_date", "review_answer_timestamp"),
        numeric_columns=("review_score",),
        date_columns=("review_creation_date", "review_answer_timestamp"),
    ),
    SourceSpec(
        "olist_orders_dataset.csv", "orders",
        ("order_id", "customer_id", "order_status", "order_purchase_timestamp", "order_approved_at", "order_delivered_carrier_date", "order_delivered_customer_date", "order_estimated_delivery_date"),
        ("order_id",),
        date_columns=("order_purchase_timestamp", "order_approved_at", "order_delivered_carrier_date", "order_delivered_customer_date", "order_estimated_delivery_date"),
    ),
    SourceSpec(
        "olist_products_dataset.csv", "products",
        ("product_id", "product_category_name", "product_name_lenght", "product_description_lenght", "product_photos_qty", "product_weight_g", "product_length_cm", "product_height_cm", "product_width_cm"),
        ("product_id",),
        numeric_columns=("product_name_lenght", "product_description_lenght", "product_photos_qty", "product_weight_g", "product_length_cm", "product_height_cm", "product_width_cm"),
    ),
    SourceSpec(
        "olist_sellers_dataset.csv", "sellers",
        ("seller_id", "seller_zip_code_prefix", "seller_city", "seller_state"),
        ("seller_id",),
    ),
    SourceSpec(
        "product_category_name_translation.csv", "category_translation",
        ("product_category_name", "product_category_name_english"),
        ("product_category_name",),
    ),
)
