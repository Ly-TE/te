< !DOCTYPE
html >
< html
lang = "zh-CN" >
< head >
< meta
charset = "UTF-8" >
< meta
name = "viewport"
content = "width=device-width, initial-scale=1.0" >
< title > 提车检验手册 < / title >
< script
src = "https://cdn.sheetjs.com/xlsx-0.19.3/package/dist/xlsx.full.min.js" > < / script >
< style >
body
{
    font - family: Arial, sans - serif;
margin: 20
px;
}
h2
{
    text - align: center;
color:  # 333;
}
table
{
    width: 100 %;
border - collapse: collapse;
margin - bottom: 20
px;
}
th, td
{
    border: 1px solid  # ddd;
    padding: 8px;
text - align: left;
}
th
{
    background - color:  # f2f2f2;
        font - weight: bold;
}
tr: nth - child(even)
{
    background - color:  # f9f9f9;
}
.section - title
{
    background - color:  # e6e6e6;
        font - weight: bold;
}
button
{
    padding: 10px 15px;
background - color:  # 4CAF50;
color: white;
border: none;
border - radius: 4
px;
cursor: pointer;
font - size: 16
px;
}
button: hover
{
    background - color:  # 45a049;
}
< / style >
< / head >
< body >
< h2 > 提车检验手册 < / h2 >
< table
id = "inspectionTable" >
< thead >
< tr >
< th > 大项 < / th >
< th > 分项 < / th >
< th > 检查内容 < / th >
< th > 查验方法 < / th >
< th > 查验表现及判断方法 < / th >
< th > 结论 < / th >
< th > 备注 < / th >
< / tr >
< / thead >
< tbody >
< tr


class ="section-title" >

< td
colspan = "7" > 一、随车资料的检查 < / td >
< / tr >
< tr >
< td > 随车资料的检查 < / td >
< td > 购车发票 < / td >
< td > 购车发票是购车时最重要的证明，同时也是汽车上户时的凭证之一。并要确认其有效性 < / td >
< td > 无 < / td >
< td > 以上部分的各项单据 / 凭证必须认真检查，如果发现有任何的遗漏、错误都必须要求销售商立刻解决，否则将影响您上牌照、日后的保修等内容。 < / td >
< td > 有 / 无 < / td >
< td > 无 < / td >
< / tr >
< tr >
< td > 随车资料的检查 < / td >
< td > 车辆合格证 < / td >
< td > 汽车上户时必备，合格证是汽车另一个重要的凭证，也是汽车上户时必备的证件。只有具有合格证的汽车才符合国家对机动车装备质量及有关标准的要求。 < / td >
< td > 无 < / td >
< td > 无 < / td >
< td > 有 / 无 < / td >
< td > 无 < / td >
< / tr >
< tr >
< td > 随车资料的检查 < / td >
< td > 三包服务卡保修单 < / td >
< td > 汽车在一定时间和行驶里程内，凭三包服务卡可以享受厂家的无偿服务，但不包括灯泡、橡胶等汽车易损件不包括在内。保修单上必须有4S的印章，证明是4S正式发的货 < / td >
< td > 无 < / td >
< td > 无 < / td >
< td > 有 / 无 < / td >
< td > 无 < / td >
< / tr >
< tr >
< td > 随车资料的检查 < / td >
< td > 车辆使用说明书 < / td >
< td > 用户必须按照车辆使用说明书的要求合理使用车辆。若不按使用说明书的要求使用而造成的车辆损害，厂家不负责三包。使用说明书同时注明了车辆的主要技术参数和维护调校所必须的技术数据，是修车时的参照文本。 < / td >
< td > 无 < / td >
< td > 无 < / td >
< td > 有 / 无 < / td >
< td > 无 < / td >
< / tr >

< tr


class ="section-title" >

< td
colspan = "7" > 二、启动前的车外检查 < / td >
< / tr >
< tr >
< td > 启动前的车外检查 < / td >
< td > 日期检查 < / td >
< td >
1.
核对车辆铭牌识别代码跟车辆合格证是否一致 < br >
2.
查看玻璃生产日期 < br >
& nbsp; & nbsp;
生产日期要早于车辆生产日期 < br >
& nbsp; & nbsp;
玻璃生产日期一致，不能相差3个月 < br >
3.
查看轮胎生产日期，生产日期要早于车辆生产日期 < br >
& nbsp; & nbsp;
生产日期要早于车辆生产日期 < br >
& nbsp; & nbsp;
四条轮胎生产日期一致，不能相差3个月
< / td >
< td > 无 < / td >
< td > 无 < / td >
< td > 有 / 无 < / td >
< td > 无 < / td >
< / tr >
< tr >
< td > 启动前的车外检查 < / td >
< td > 车身平整度 < / td >
< td > 检查车身钢板平整度 < / td >
< td > 无 < / td >
< td > 有无非正常凹、凸起伏 < / td >
< td > 有 / 无 < / td >
< td > 无 < / td >
< / tr >
< tr >
< td > 启动前的车外检查 < / td >
< td > 保险杠的平整度 < / td >
< td > 检查保险杠平整度 < / td >
< td > 无 < / td >
< td > 有无非正常凹、凸起伏 < / td >
< td > 有 / 无 < / td >
< td > 无 < / td >
< / tr >
< / tbody >
< / table >
< button
onclick = "downloadExcel()" > 下载Excel < / button >

< script >
function
downloadExcel()
{
// 获取表格元素
const
table = document.getElementById('inspectionTable');

// 将表格转换为工作簿
const
wb = XLSX.utils.table_to_book(table, {sheet: "提车检验手册"});

// 生成Excel文件并下载
XLSX.writeFile(wb, "提车检验手册.xlsx");
}
< / script >
< / body >
< / html >