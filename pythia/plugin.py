__license__ = "BSD-3-Clause"

import logging
from enum import Enum, unique


@unique
class PluginHook(Enum):
    post_config = 100
    pre_build_context = 200
    post_build_context = 300
    post_peerless_pixel_success = 350
    post_peerless_pixel_skip = 351
    post_compose_peerless_pixel_success = 352
    post_compose_peerless_pixel_skip = 353
    post_compose_peerless_all = 354
    post_setup = 400
    pre_run = 500
    run_pixel = 600
    post_run_pixel_success = 650
    post_run_pixel_failed = 651
    post_run_all = 700
    pre_analytics = 800
    post_analytics = 900


def register_plugin_function(hook, fun, config, plugins):
    # Check to see if the hook is a PluginHook
    if not isinstance(hook, PluginHook):
        logging.warning(
            "[PLUGIN] Ignoring {} because {} is not a PluginHook".format(fun, hook)
        )
        return plugins

    # Check to see if the function is a function.
    if not callable(fun):
        logging.warning(
            "[PLUGIN] Ignoring {} because {} is not a function.".format(fun, fun)
        )
        return plugins

    # Check to see if the config is an object.
    if not isinstance(config, dict):
        logging.warning(
            "[PLUGIN] Ignoring {} because {} is not a valid configuration".format(
                fun, config
            )
        )
        return plugins

    # Check to see if the plugin is being multicalled in that hook
    if hook in plugins:
        for entries in plugins[hook]:
            if entries["fun"] == fun:
                logging.warning(
                    "[PLUGIN] Ignoring {} because it already exists in the hook {}".format(
                        fun, hook
                    )
                )
                return plugins

    _plugins = {**plugins}
    if hook in _plugins:
        # Check to see if this function is already in there.
        _plugins[hook].append({"fun": fun, "config": config})
    else:
        _plugins[hook] = [{"fun": fun, "config": config}]
    return _plugins


def load_plugins(config, plugins={}, module_prefix="pythia.plugins"):
    # Check the configuration file for plugins
    logging.info("[PLUGIN] Starting the plugin check...")
    plugin_config = config.get("plugins", {})
    if plugin_config == {}:
        logging.info("[PLUGIN] No plugins required")
        return plugins
    _imported = {}

    # Check to see if the plugins are in place
    import importlib.util

    for plugin in plugin_config:
        logging.info("[PLUGIN] Plug in {} found".format(plugin["plugin"]))
        if "plugin" not in plugin:
            logging.warning("[PLUGIN] Invalid plugin configuration: {}".format(plugin))
            continue
        spec = importlib.util.find_spec("{}.{}".format(module_prefix, plugin["plugin"]))
        if spec is None:
            logging.warning("[PLUGIN] Cannot find plugin: {}".format(plugin["plugin"]))
            continue
        _loaded = importlib.import_module(
            "{}.{}".format(module_prefix, plugin["plugin"])
        )
        # TODO: Check to see if the config works for the plugin
        # TODO: Check to see if the plugin conforms to the correct signature (optional)

        # Call plugin initialization
        _imported = _loaded.initialize(plugin, _imported, config)
    return _imported


def run_plugin_functions(hook, plugins, **kwargs):
    _return = {**kwargs}
    if hook in plugins:
        for plugin_fun in plugins[hook]:
            plugin_fun_return = plugin_fun["fun"](plugin_fun.get("config", {}), _return, **kwargs)
            _return = {
                **_return,
                **({} if plugin_fun_return is None else plugin_fun_return)
            }

    return _return
