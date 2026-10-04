from scanner.config_loader import ConfigManager

# Test loading
config = ConfigManager(env='production')

# Test all environments
for env in ['development', 'staging', 'production']:
    c = ConfigManager(env=env)
    print(f"{env}: max_critical = {c.get_max_vulnerabilities_allowed('CRITICAL')}")
