global MtMaxMenuTitle = "Mt Max"

fn MtMaxUnregisterMenuItem = (
    menu = menuMan.findMenu MtMaxMenuTitle
    while menu != undefined do (
        menuMan.unRegisterMenu menu
        menuMan.updateMenuBar()
        menu = menuMan.findMenu MtMaxMenuTitle
    )
)

-- The macro can't reference any variables because they haven't been assigned at load time
fn MtMaxDefineOpenPluginMacro = (
    src = "macroScript MtMaxOpenPluginMacro category:\"" + MtMaxMenuTitle + "\" ( python.ExecuteFile \"" + ( substituteString MtMaxEntrypointFilePath "\\" "\\\\" ) + "\" )"
    execute src
)

fn MtMaxRegisterMenuItem = (
    MtMaxUnregisterMenuItem()
    mainMenu = menuMan.getMainMenuBar()
    menu = menuMan.createMenu MtMaxMenuTitle 
    subMenu = menuMan.createSubMenuItem MtMaxMenuTitle menu
    mainMenu.addItem subMenu (mainMenu.numItems()+1)
    MtMaxDefineOpenPluginMacro()
    action = menuMan.createActionItem "MtMaxOpenPluginMacro" MtMaxMenuTitle
    action.setTitle "Open plugin"
    action.setUseCustomTitle true
    menu.addItem action (menu.numItems()+1)
    menuMan.updateMenuBar()
)
MtMaxRegisterMenuItem()