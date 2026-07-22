小米买埋点事件对应的羚羊事件如下
APP_ACTIVE("APP_ACTIVE", "client_install"),
    APP_REGISTER("APP_REGISTER", "login_on"),
    APP_PAY("APP_PAY", "payment_successful"),


小米埋点事件
自定义激活APP_ACTIVE，触发条件：小米广告渠道下载安装 APP，打开后完成登录，不限制是否为首次登录；只要登录成功就上报（例如老设备二次登录、注册后重复登录场景）
自定义注册APP_REGISTER，触发条件：小米广告渠道下载安装 APP，首次打开并完成登录，仅限设备第一次登录行为；仅首登上报 1 次，后续重复登录只走激活事件，不再上报注册。
付费APP_PAY：只要通过付费广告下载的app，在app里面的付费行为都上报