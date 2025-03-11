def build_templates_table_data(items):
    """
    Process items from the templates table and return structured data.

    Args:
        items (list): List of items from the templates table.

    Returns:
        list: List of dictionaries with structured templates data.
    """
    templates_table_dict = []

    for jsonitem in items:
        templates_data = {}
        templates_data['templateId'] = jsonitem.get('templateId', None)
        templates_data['templateName'] = jsonitem.get('templateName', None)
        templates_data['version'] = jsonitem.get('version', None)
        templates_data['defaultDemandConfig'] = jsonitem.get('defaultDemandConfig', None)
        templates_table_dict.append(templates_data)

    return templates_table_dict
