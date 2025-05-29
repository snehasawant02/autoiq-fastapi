def predict_lead_category(sales_series):
    thresholds = {
        "High": 100000,
        "Medium": 50000
    }
    categories = []
    for sale in sales_series:
        if sale >= thresholds["High"]:
            categories.append("High")
        elif sale >= thresholds["Medium"]:
            categories.append("Medium")
        else:
            categories.append("Low")
    return categories
