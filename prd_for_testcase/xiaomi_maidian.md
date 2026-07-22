事件英文名	事件中文名	属性英文名	属性中文名	数据类型	属性值示例或说明	应埋点平台	上报时机	责任端	处理人	备注															
page_exposure	页面曝光事件	cur_page_category		str	game_acceleration_leishen:游戏开始加速页面
recharge_leishen：付费/订阅页面
acceleration_results_leishen：加速结果页面
order_leishen:订单页面																				
		page_package_name	页面app包名	str	xxx.xxx																				
item_exposure	元素曝光事件	item_type	元素类型	str	button：按钮
pop：弹窗																				
		item_enum	元素类型细分	str	button下：start_accelerating_leishen：开始加速按钮
button下：pay_leishen：付费充值按钮
button下：open_leishen：游戏启动按钮
button下：stop_accelerate_leishen：关闭加速按钮

pop下：service_switch_leishen：服务切换弹窗
pop下：time_limit_leishen：时间限制弹窗																				
		package_name	包名信息	str	xxx.xxx																				
item_click	元素点击事件	item_type	元素类型	str	button：按钮																				
		item_enum	元素类型细分	str	button下：start_accelerating_leishen：开始加速按钮
button下：pay_leishen：付费充值按钮
button下：open_leishen：游戏启动按钮
button下：stop_accelerate_leishen：关闭加速按钮
																				
		package_name	包名信息	str	xxx.xxx																				
api_request		api_path	请求路径	str	accelerate_leishen																				
		type	请求类型	str	acceleration_request_leishen:加速请求
acceleration_success_leishen:加速成功
acceleration_failure_leishen:加速失败
start_game_leishen:启动游戏																				