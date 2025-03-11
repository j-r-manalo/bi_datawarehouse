from itc_common_utilities.logger.logger_setup import setup_logger

# Initialize the logger
logger = setup_logger(__name__)


def build_templates_table_data(items):
    """
    Process items from the templates table and return structured data.

    Args:
        items (list): List of items from the templates table.

    Returns:
        list: List of dictionaries with structured templates data.
    """
    logger.info(f"Building templates data from {len(items)} template items")
    templates_table_dict = []
    missing_data_count = 0

    for index, jsonitem in enumerate(items):
        template_id = jsonitem.get('templateId', 'unknown')
        logger.debug(f"Processing template {template_id} (item {index + 1} of {len(items)})")

        templates_data = {}
        templates_data['templateId'] = jsonitem.get('templateId', None)
        templates_data['templateName'] = jsonitem.get('templateName', None)
        templates_data['version'] = jsonitem.get('version', None)
        templates_data['defaultDemandConfig'] = jsonitem.get('defaultDemandConfig', None)

        # Check if any important fields are missing
        missing_fields = [field for field in ['templateId', 'templateName', 'version']
                          if jsonitem.get(field) is None]

        if missing_fields:
            missing_data_count += 1
            logger.warning(f"Template item {template_id} is missing required fields: {', '.join(missing_fields)}")

        templates_table_dict.append(templates_data)
        logger.debug(f"Successfully processed template {template_id}")

    logger.info(f"Completed template data processing. Created {len(templates_table_dict)} template records")
    logger.info(f"Found {missing_data_count} templates with missing data fields")

    return templates_table_dict