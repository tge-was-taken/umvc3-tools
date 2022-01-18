global MtMaxMenuTitle = "Mt Max"

macroScript MtMaxOpenPluginMacro category:MtMaxMenuTitle
(
	python.ExecuteFile MtMaxEntrypointFilePath
)

fn MtMaxUnregisterMenuItem = (
    menu = menuMan.findMenu MtMaxMenuTitle
    while menu != undefined do (
        menuMan.unRegisterMenu menu
        menuMan.updateMenuBar()
        menu = menuMan.findMenu MtMaxMenuTitle
    )
)

fn MtMaxRegisterMenuItem = (
    MtMaxUnregisterMenuItem()
    mainMenu = menuMan.getMainMenuBar()
    menu = menuMan.createMenu MtMaxMenuTitle 
    subMenu = menuMan.createSubMenuItem MtMaxMenuTitle menu
    mainMenu.addItem subMenu (mainMenu.numItems()+1)
    action = menuMan.createActionItem "MtMaxOpenPluginMacro" MtMaxMenuTitle
    action.setTitle "Open plugin"
    action.setUseCustomTitle true
    menu.addItem action (menu.numItems()+1)
    menuMan.updateMenuBar()
)
MtMaxRegisterMenuItem()