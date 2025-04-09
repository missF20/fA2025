from main import app

print("Available API routes:")
print("-" * 80)

for rule in app.url_map.iter_rules():
    if "static" not in str(rule) and "favicon" not in str(rule):
        methods = ', '.join(rule.methods)
        print(f"{str(rule):50s} [{methods}]")