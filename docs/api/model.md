# Model API Reference

A classe `Model` é o coração da CaspyORM. Ela fornece uma interface familiar para trabalhar com tabelas do Cassandra.

## Classe Model

::: caspyorm.model.Model
    handler: python
    selection:
      members:
        - __init__
        - save
        - save_async
        - update
        - update_async
        - create
        - create_async
        - bulk_create
        - bulk_create_async
        - get
        - get_async
        - filter
        - all
        - as_pydantic
        - to_pydantic_model
        - sync_table
        - sync_table_async
        - delete
        - delete_async
        - update_collection
        - update_collection_async
        - create_model
        - model_dump
        - model_dump_json
    rendering:
      show_source: true
      show_root_heading: true
      show_category_heading: true
      show_signature_annotations: true
      show_bases: true
      heading_level: 3
      members_order: source
      docstring_style: google
      preload_modules: true
      filters: ["!^_"]
      merge_init_into_class: true 