# 商品类目中文映射核对表

来源为本机Olist官方版本2的product_category_name_translation.csv（71行），与真实API的74个选项逐项核对。中文译名及用户指定的原名仅用于界面展示，原编码、统计分组及API值不变；同名带数字类目保留独立项，不自行合并。

- `cool_stuff`、`la_cuisine`：按用户最终指定，界面分别显示 **Cool Stuff**、**La Cuisine**，保留原名，不强行赋予中文商品含义。
- `seguros_e_servicos`：按用户最终指定，界面显示 **Seguros e Serviços**。官方英文仍保留security_and_services，原葡语编码、统计及导出均不变。
- `pc_gamer`：官方翻译缺失，按原编码PC + gamer补充“游戏电脑”。
- `portateis_cozinha_e_preparadores_de_alimentos`：官方缺失，按葡语组成词补充字面译名“厨房便携器具与食品处理设备”；不推断具体SKU。
- `__unknown__`为仓库未分类标识，不是源表英文译名，显示“未分类”。未来未识别编码统一回退“未翻译”。指定保留原名的三项使用preserved_name状态；搜索支持展示名称、原码和原官方英文。原码提示、CSV原字段与本表可追溯。

核对来源：[Olist/Kaggle](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)、[Priberam portátil](https://dicionario.priberam.org/port%C3%A1til)、[preparador](https://dicionario.priberam.org/preparador)、[seguro](https://dicionario.priberam.org/seguro)。补充译名基于字面语义，不声称是Olist官方中文翻译。CC BY-NC-SA 4.0；此映射不含订单或用户记录。

| 原编码 | 官方英文 | 界面展示 | 核对状态 |
|---|---|---|---|
| `__unknown__` | 官方未收录 | 未分类 | missing |
| `agro_industria_e_comercio` | agro_industry_and_commerce | 农业与工商业用品 | translated |
| `alimentos` | food | 食品 | translated |
| `alimentos_bebidas` | food_drink | 食品与饮料 | translated |
| `artes` | art | 艺术品 | translated |
| `artes_e_artesanato` | arts_and_craftmanship | 艺术与手工艺 | translated |
| `artigos_de_festas` | party_supplies | 派对用品 | translated |
| `artigos_de_natal` | christmas_supplies | 圣诞用品 | translated |
| `audio` | audio | 音响设备 | translated |
| `automotivo` | auto | 汽车用品 | translated |
| `bebes` | baby | 母婴用品 | translated |
| `bebidas` | drinks | 饮料 | translated |
| `beleza_saude` | health_beauty | 美容与健康 | translated |
| `brinquedos` | toys | 玩具 | translated |
| `cama_mesa_banho` | bed_bath_table | 床品、餐桌与卫浴用品 | translated |
| `casa_conforto` | home_confort | 家居舒适用品 | translated |
| `casa_conforto_2` | home_comfort_2 | 家居舒适用品（二） | translated |
| `casa_construcao` | home_construction | 家居建材 | translated |
| `cds_dvds_musicais` | cds_dvds_musicals | 音乐光盘 | translated |
| `cine_foto` | cine_photo | 摄影与影像 | translated |
| `climatizacao` | air_conditioning | 空调与温控 | translated |
| `consoles_games` | consoles_games | 游戏机与游戏 | translated |
| `construcao_ferramentas_construcao` | construction_tools_construction | 建筑施工用品 | translated |
| `construcao_ferramentas_ferramentas` | costruction_tools_tools | 施工工具 | translated |
| `construcao_ferramentas_iluminacao` | construction_tools_lights | 建筑照明 | translated |
| `construcao_ferramentas_jardim` | costruction_tools_garden | 园艺施工用品 | translated |
| `construcao_ferramentas_seguranca` | construction_tools_safety | 施工安全用品 | translated |
| `cool_stuff` | cool_stuff | Cool Stuff | preserved_name |
| `dvds_blu_ray` | dvds_blu_ray | DVD与蓝光碟 | translated |
| `eletrodomesticos` | home_appliances | 家用电器 | translated |
| `eletrodomesticos_2` | home_appliances_2 | 家用电器（二） | translated |
| `eletronicos` | electronics | 电子产品 | translated |
| `eletroportateis` | small_appliances | 小家电 | translated |
| `esporte_lazer` | sports_leisure | 运动与休闲 | translated |
| `fashion_bolsas_e_acessorios` | fashion_bags_accessories | 时尚箱包与配饰 | translated |
| `fashion_calcados` | fashion_shoes | 鞋靴 | translated |
| `fashion_esporte` | fashion_sport | 运动服饰 | translated |
| `fashion_roupa_feminina` | fashio_female_clothing | 女装 | translated |
| `fashion_roupa_infanto_juvenil` | fashion_childrens_clothes | 儿童与青少年服装 | translated |
| `fashion_roupa_masculina` | fashion_male_clothing | 男装 | translated |
| `fashion_underwear_e_moda_praia` | fashion_underwear_beach | 内衣与沙滩服饰 | translated |
| `ferramentas_jardim` | garden_tools | 园艺工具 | translated |
| `flores` | flowers | 鲜花 | translated |
| `fraldas_higiene` | diapers_and_hygiene | 纸尿裤与卫生用品 | translated |
| `industria_comercio_e_negocios` | industry_commerce_and_business | 工商业用品 | translated |
| `informatica_acessorios` | computers_accessories | 电脑与配件 | translated |
| `instrumentos_musicais` | musical_instruments | 乐器 | translated |
| `la_cuisine` | la_cuisine | La Cuisine | preserved_name |
| `livros_importados` | books_imported | 进口图书 | translated |
| `livros_interesse_geral` | books_general_interest | 综合图书 | translated |
| `livros_tecnicos` | books_technical | 技术图书 | translated |
| `malas_acessorios` | luggage_accessories | 旅行箱包与配件 | translated |
| `market_place` | market_place | 综合集市 | translated |
| `moveis_colchao_e_estofado` | furniture_mattress_and_upholstery | 床垫与软体家具 | translated |
| `moveis_cozinha_area_de_servico_jantar_e_jardim` | kitchen_dining_laundry_garden_furniture | 厨房、餐厅、洗衣区与花园家具 | translated |
| `moveis_decoracao` | furniture_decor | 家具与装饰 | translated |
| `moveis_escritorio` | office_furniture | 办公家具 | translated |
| `moveis_quarto` | furniture_bedroom | 卧室家具 | translated |
| `moveis_sala` | furniture_living_room | 客厅家具 | translated |
| `musica` | music | 音乐用品 | translated |
| `papelaria` | stationery | 文具 | translated |
| `pc_gamer` | 官方未收录 | 游戏电脑 | supplemental |
| `pcs` | computers | 电脑 | translated |
| `perfumaria` | perfumery | 香水与香氛 | translated |
| `pet_shop` | pet_shop | 宠物用品 | translated |
| `portateis_casa_forno_e_cafe` | small_appliances_home_oven_and_coffee | 家用烤箱与咖啡小电器 | translated |
| `portateis_cozinha_e_preparadores_de_alimentos` | 官方未收录 | 厨房便携器具与食品处理设备 | supplemental |
| `relogios_presentes` | watches_gifts | 钟表与礼品 | translated |
| `seguros_e_servicos` | security_and_services | Seguros e Serviços | preserved_name |
| `sinalizacao_e_seguranca` | signaling_and_security | 标识与安全用品 | translated |
| `tablets_impressao_imagem` | tablets_printing_image | 平板、打印与成像设备 | translated |
| `telefonia` | telephony | 通信设备 | translated |
| `telefonia_fixa` | fixed_telephony | 固定电话 | translated |
| `utilidades_domesticas` | housewares | 家居日用品 | translated |
