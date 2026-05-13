# entity_share_data 字段说明

> 库: `goin_new` | 总列数: 346 | 更新时间: 2026-05-12

按内容语义分组，便于快速理解表结构。

---

## 一、基础标识与元信息 (6 列)

| 字段 | 类型 | 说明 |
|---|---|---|
| `mongo_id` | String | MongoDB 唯一 ID |
| `name` | String | 实体名称 |
| `nonnative_names` | Array(String) | 非原生语言名称（如中文名） |
| `aliases` | Array(String) | 别名 |
| `type` | String | 实体类型 |
| `meta_type` | String | 元类型 |
| `subtype` | String | 子类型 |

---

## 二、联系方式 (14 列)

| 字段 | 类型 | 说明 |
|---|---|---|
| `phone_number` | Array(String) | 手机号 |
| `telephone` | Array(String) | 座机号 |
| `email` | Array(String) | 邮箱 |
| `fax` | Array(String) | 传真 |
| `contact_phone_number` | Array(String) | 联系电话 |
| `social_media_account` | Array(String) | 社交媒体账号 |
| `personal_website_account` | Array(String) | 个人网站 |
| `official_website` | Array(String) | 官方网站 |
| `facebook_id` | Array(String) | Facebook |
| `twitter_username` | Array(String) | Twitter/X |
| `official_app` | Array(String) | 官方 App |
| `call_sign` | Array(String) | 呼号/信号符 |
| `pennant_number` | Array(String) | 舷号/编号 |
| `post_num` | Int32 | 邮编 |

---

## 三、人口统计学 (14 列)

| 字段 | 类型 | 说明 |
|---|---|---|
| `sex_or_gender` | String | 性别 |
| `age` | Int32 | 年龄 |
| `date_of_birth` | Int64 | 出生日期（时间戳） |
| `date_of_death` | Int64 | 死亡日期（时间戳） |
| `place_of_birth` | Array(String) | 出生地 |
| `place_of_death` | String | 死亡地点 |
| `manner_of_death` | String | 死亡方式 |
| `cause_of_death` | String | 死因 |
| `ethnic_group` | Array(String) | 民族 |
| `religion` | Array(String) | 宗教信仰 |
| `country_of_citizenship` | Array(String) | 国籍 |
| `ancestral_home` | String | 籍贯/祖籍 |
| `native_language` | String | 母语 |
| `language_of_work` | String | 工作语言 |

---

## 四、家庭与亲属关系 (8 列)

| 字段 | 类型 | 说明 |
|---|---|---|
| `father` | String | 父亲 |
| `mother` | String | 母亲 |
| `spouse` | Array(String) | 配偶 |
| `unmarried_partner` | String | 未婚伴侣 |
| `sibling` | Array(String) | 兄弟姐妹 |
| `child` | Array(String) | 子女 |
| `families` | Int32 | 家庭数量 |
| `isMarry` | Int64 | 婚姻状态 |

---

## 五、教育背景 (10 列)

| 字段 | 类型 | 说明 |
|---|---|---|
| `education_background` | String | 教育背景概述 |
| `academic_degree` | Array(String) | 学位 |
| `school` | String | 学校 |
| `academic_major` | String | 专业 |
| `education_experience.edu_start_time` | Array(Int32) | 教育经历 — 开始时间 |
| `education_experience.edu_end_time` | Array(Int32) | 教育经历 — 结束时间 |
| `education_experience.edu_school` | Array(String) | 教育经历 — 学校 |
| `education_experience.edu_academic_degree` | Array(String) | 教育经历 — 学位 |
| `education_experience.edu_academic_major` | Array(String) | 教育经历 — 专业 |
| `alma_mater` | Array(String) | 母校（另有独立字段） |

---

## 六、职业与职位 (16 列)

| 字段 | 类型 | 说明 |
|---|---|---|
| `occupation` | Array(String) | 职业 |
| `title` | String | 头衔/职称 |
| `position_held` | Array(String) | 曾担任职位 |
| `professional_division` | Array(String) | 专业领域/部门 |
| `department_or_company` | String | 所属部门/公司 |
| `employee` | Array(String) | 雇员 |
| `members_have_occupation` | Array(String) | 成员职业分布 |
| `position_experience.pos_start_time` | Array(Int32) | 任职经历 — 开始时间 |
| `position_experience.pos_end_time` | Array(Int32) | 任职经历 — 结束时间 |
| `position_experience.pos_department_or_company` | Array(String) | 任职经历 — 单位 |
| `position_experience.position` | Array(String) | 任职经历 — 职位 |
| `employer` | Array(String) | 雇主 |
| `work_location` | Array(String) | 工作地点 |
| `member_of` | Array(String) | 隶属组织 |
| `residence` | Array(String) | 居住地 |
| `hometown` | Array(String) | 家乡 |

---

## 七、组织信息 (24 列)

| 字段 | 类型 | 说明 |
|---|---|---|
| `legal_form` | String | 法律形式（如有限公司） |
| `industry` | String | 行业 |
| `business_division` | Array(String) | 业务部门 |
| `business_model` | String | 商业模式 |
| `founded_by` | String | 创始人 |
| `owner` | String | 所有者 |
| `parent_organization` | Array(String) | 上级组织 |
| `subsidiary` | Array(String) | 下属机构 |
| `director_of_the_organization` | String | 组织主任/董事 |
| `chief_executive_officer` | String | CEO |
| `chief_operating_officer` | String | COO |
| `secretary_general` | String | 秘书长 |
| `leader` | Array(String) | 领导人 |
| `member_count.member_count_value` | Array(Int32) | 成员数量 |
| `member_count.member_count_time` | Array(Int64) | 成员数量 — 统计时间 |
| `member_count.member_count_unit` | Array(String) | 成员数量 — 单位 |
| `employee_number.employee_number_value` | Array(Int32) | 员工数 |
| `employee_number.employee_number_time` | Array(Int64) | 员工数 — 统计时间 |
| `employee_number.employee_number_unit` | Array(String) | 员工数 — 单位 |
| `number_of_hospital_beds` | Int32 | 医院床位数 |
| `operating_area` | Array(String) | 运营区域 |
| `planning` | String | 规划 |
| `stock_exchange` | Array(String) | 上市交易所 |
| `production` | Array(String) | 产品产出 |

---

## 八、政治与政府 (24 列)

| 字段 | 类型 | 说明 |
|---|---|---|
| `political_ideology` | Array(String) | 政治意识形态 |
| `political_faction` | Array(String) | 政治派别 |
| `political_status` | String | 政治面貌 |
| `political_leaning` | String | 政治倾向 |
| `member_of_political_party` | Array(String) | 政党成员 |
| `executive_branch` | String | 行政部门 |
| `legislature` | Array(String) | 立法机构 |
| `basic_form_of_government` | Array(String) | 政体 |
| `highest_judicial_authority` | Array(String) | 最高司法机构 |
| `countries_covered_by_jurisdiction` | Array(String) | 管辖覆盖国家 |
| `driving_side` | String | 行驶方向（左/右舵） |
| `national_anthem` | String | 国歌 |
| `currency` | String | 货币 |
| `country_calling_code` | String | 国家电话区号 |
| `emergency_phone_number` | Array(String) | 紧急电话 |
| `top_level_domain` | Array(String) | 顶级域名 |
| `official_language` | Array(String) | 官方语言 |
| `flag` | String | 国旗/旗帜 |
| `official_symbol` | String | 官方标志/国徽 |
| `public_holiday` | Array(String) | 公共假日 |
| `contains_administrative_territorial_entity` | Array(String) | 包含的行政区划 |
| `shares_border_with` | Array(String) | 接壤国家/地区 |
| `time_zone` | Array(String) | 时区 |
| `capital.capital_value` | Array(String) | 首都 |
| `capital.capital_start_time` | Array(Int64) | 首都 — 起始时间 |
| `capital.capital_end_time` | Array(Int64) | 首都 — 结束时间 |

---

## 九、军事 (30 列)

| 字段 | 类型 | 说明 |
|---|---|---|
| `military_rank` | Array(String) | 军衔 |
| `military_branch` | Array(String) | 军种/兵种 |
| `arm_of_the_services` | Array(String) | 武装力量分支 |
| `commanded_by` | Array(String) | 指挥官 |
| `deputy_commanded_by` | Array(String) | 副指挥官 |
| `chief_of_staff` | Array(String) | 参谋长 |
| `battle_group` | Array(String) | 战斗群 |
| `subordinate_fleet` | Array(String) | 下属舰队 |
| `garrison` | Array(String) | 驻军/ garrison |
| `total_armed_forces` | Int32 | 武装部队总人数 |
| `vessel_class` | Array(String) | 舰船级别 |
| `warship_captain.warship_captain_value` | Array(String) | 舰长 |
| `warship_captain.warship_captain_start_time` | Array(Int64) | 舰长 — 上任时间 |
| `warship_captain.warship_captain_end_time` | Array(Int64) | 舰长 — 离任时间 |
| `armament.armament_name` | Array(String) | 武器装备名称 |
| `armament.armament_number` | Array(Int32) | 武器装备数量 |
| `armament.armament_unit` | Array(String) | 武器装备单位 |
| `caliber.caliber_value` | Array(Float32) | 口径 |
| `caliber.caliber_unit` | Array(String) | 口径单位 |
| `close_in_weapon` | Array(String) | 近防武器 |
| `firing_range.firing_range_value` | Float32 | 射程 |
| `firing_range.firing_range_unit` | String | 射程单位 |
| `muzzle_velocity` | Float32 | 初速 |
| `combat_radius.combat_radius_value` | Float32 | 作战半径 |
| `combat_radius.combat_radius_unit` | String | 作战半径单位 |
| `detection_distance.detection_distance_value` | Float32 | 探测距离 |
| `detection_distance.detection_distance_unit` | String | 探测距离单位 |
| `service_entry` | Int64 | 服役时间 |
| `service_retirement` | Int64 | 退役时间 |
| `first_flight` | Int64 | 首飞时间 |
| `crew_member` | Array(String) | 船员/机组成员 |
| `power_system` | Array(String) | 动力系统 |
| `cruise_speed.cruise_speed_value` | Float32 | 巡航速度 |
| `cruise_speed.cruise_speed_unit` | String | 巡航速度单位 |

---

## 十、地理位置 (22 列)

| 字段 | 类型 | 说明 |
|---|---|---|
| `headquarters_location` | Array(String) | 总部所在地 |
| `continent` | Array(String) | 大洲 |
| `country` | Array(String) | 国家 |
| `located_in_or_next_to_body_of_water` | Array(String) | 濒临水域 |
| `coordinate_location.longitude` | Float64 | 经度 |
| `coordinate_location.latitude` | Float64 | 纬度 |
| `geoshape` | String | 地理形状（GeoJSON） |
| `address` | Array(String) | 地址 |
| `street_address` | String | 街道地址 |
| `place` | String | 地点 |
| `located_in_the_administrative_territorial_entity` | String | 所属行政区 |
| `contains_settlement` | Array(String) | 包含的聚居点 |
| `home_port` | String | 母港 |
| `service_city` | Array(String) | 服务城市 |
| `local_dialing_code` | Array(String) | 本地拨号代码 |
| `postal_code` | Array(String) | 邮政编码 |
| `location_of_creation` | Array(String) | 创建地点 |
| `location_of_formation` | String | 成立地点 |
| `aerodrome_reference_point` | String | 机场基准点 |
| `place_of_birth` | Array(String) | 出生地 |
| `place_of_death` | String | 死亡地点 |
| `ancestral_home` | String | 祖籍 |

---

## 十一、经济与金融 (16 列)

| 字段 | 类型 | 说明 |
|---|---|---|
| `gdp.gdp_value` | Array(Float32) | GDP 值 |
| `gdp.gdp_time` | Array(Int64) | GDP — 统计时间 |
| `gdp.gdp_unit` | Array(String) | GDP — 单位 |
| `population.population_value` | Array(Int32) | 人口 |
| `population.population_time` | Array(Int64) | 人口 — 统计时间 |
| `population.population_unit` | Array(String) | 人口 — 单位 |
| `gini_coefficient.gini_coefficient_value` | Array(Float32) | 基尼系数 |
| `gini_coefficient.gini_coefficient_time` | Array(Int64) | 基尼系数 — 统计时间 |
| `unemployment` | Float32 | 失业率 |
| `total_assets` | Float32 | 总资产 |
| `price.price_value` | Float32 | 价格 |
| `price.price_unit` | String | 价格单位 |
| `cost.cost_value` | Array(Float32) | 成本 |
| `cost.cost_time` | Array(Int64) | 成本 — 统计时间 |
| `cost.cost_unit` | Array(String) | 成本单位 |
| `patron_num.patron_num_value` | Array(Float32) | 赞助/客户数量 |
| `patron_num.patron_num_time` | Array(Int64) | 赞助/客户数量 — 统计时间 |
| `patron_num.patron_num_unit` | Array(String) | 赞助/客户数量 — 单位 |
| `total_produced.total_produced_value` | Array(Int32) | 总产量 |
| `total_produced.total_produced_time` | Array(Int64) | 总产量 — 统计时间 |
| `total_produced.total_produced_unit` | Array(String) | 总产量 — 单位 |

---

## 十二、物理尺寸与测量 (33 列)

| 字段 | 类型 | 说明 |
|---|---|---|
| `length.length_value` | Float32 | 长度 |
| `length.length_unit` | String | 长度单位 |
| `width.width_value` | Float32 | 宽度 |
| `width.width_unit` | String | 宽度单位 |
| `height.height_value` | Float32 | 高度 |
| `height.height_unit` | String | 高度单位 |
| `mass.mass_value` | Float32 | 质量/重量 |
| `mass.mass_unit` | String | 质量单位 |
| `weight.weight_value` | Float32 | 重量 |
| `weight.weight_unit` | String | 重量单位 |
| `diameter.diameter_value` | Float32 | 直径 |
| `diameter.diameter_unit` | String | 直径单位 |
| `wingspan.wingspan_value` | Float32 | 翼展 |
| `wingspan.wingspan_unit` | String | 翼展单位 |
| `area.area_value` | Array(Float32) | 面积 |
| `area.area_unit` | Array(String) | 面积单位 |
| `area.area_time` | Array(Int64) | 面积 — 统计时间 |
| `volume.volume_value` | Float32 | 体积 |
| `volume.volume_unit` | String | 体积单位 |
| `altitude.altitude_value` | Float32 | 海拔/高度 |
| `altitude.altitude_unit` | String | 海拔单位 |
| `longest_span` | Float32 | 最大跨度 |
| `hull_length.hull_length_value` | Float32 | 船长 |
| `hull_length.hull_length_unit` | String | 船长单位 |
| `hull_width.hull_width_value` | Float32 | 船宽 |
| `hull_width.hull_width_unit` | String | 船宽单位 |
| `draft.draft_value` | Float32 | 吃水深度 |
| `draft.draft_unit` | String | 吃水单位 |
| `standard_displacement.standard_displacement_value` | Float32 | 标准排水量 |
| `standard_displacement.standard_displacement_unit` | String | 标准排水量单位 |
| `full_loaded_displacement.full_loaded_displacement_value` | Float32 | 满载排水量 |
| `full_loaded_displacement.full_loaded_displacement_unit` | String | 满载排水量单位 |
| `hangar_length.hangar_length_value` | Float32 | 机库长度 |
| `hangar_length.hangar_length_unit` | String | 机库长度单位 |
| `hangar_width.hangar_width_value` | Float32 | 机库宽度 |
| `hangar_width.hangar_width_unit` | String | 机库宽度单位 |
| `hangar_height.hangar_height_value` | Float32 | 机库高度 |
| `hangar_height.hangar_height_unit` | String | 机库高度单位 |
| `flight_deck_length.flight_deck_length_value` | Float32 | 飞行甲板长度 |
| `flight_deck_length.flight_deck_length_unit` | String | 飞行甲板长度单位 |
| `flight_deck_width.flight_deck_width_value` | Float32 | 飞行甲板宽度 |
| `flight_deck_width.flight_deck_width_unit` | String | 飞行甲板宽度单位 |
| `angled_deck_length.angled_deck_length_value` | Float32 | 斜角甲板长度 |
| `angled_deck_length.angled_deck_length_unit` | String | 斜角甲板长度单位 |
| `length_between_perpendiculars.length_between_perpendiculars_value` | Float32 | 垂线间长 |
| `length_between_perpendiculars.length_between_perpendiculars_unit` | String | 垂线间长单位 |
| `mains_voltage` | Float32 | 电源电压 |
| `power_consumed` | Float32 | 功耗 |

---

## 十三、基础设施与交通 (14 列)

| 字段 | 类型 | 说明 |
|---|---|---|
| `station_code` | String | 车站代码 |
| `number_of_platform_tracks` | Int32 | 站台轨道数 |
| `number_of_platform_faces` | Int32 | 站台面数 |
| `daily_patronage` | Int32 | 日均客流量 |
| `visitors_per_year` | Int32 | 年访客量 |
| `number_of_houses` | Int32 | 房屋数量 |
| `number_of_spans` | Int32 | 桥跨数 |
| `floors_above_ground` | Int32 | 地上层数 |
| `floors_below_ground` | Int32 | 地下层数 |
| `runway.runway_direction` | Array(String) | 跑道方向 |
| `runway.runway_length` | Array(Float32) | 跑道长度 |
| `runway.runway_width` | Array(Float64) | 跑道宽度 |
| `runway.runway_material` | Array(String) | 跑道材质 |
| `date_in_use` | Int64 | 投入使用日期 |

---

## 十四、媒体与作品 (26 列)

| 字段 | 类型 | 说明 |
|---|---|---|
| `image` | Array(String) | 图片 URL |
| `image_path` | String | 图片本地路径 |
| `logo_image` | String | Logo |
| `medias.time` | Array(Int64) | 媒体 — 时间 |
| `medias.images` | Array(String) | 媒体 — 图片 |
| `medias.contents` | Array(String) | 媒体 — 内容 |
| `notes.time` | Array(Int64) | 备注 — 时间 |
| `notes.contents` | Array(String) | 备注 — 内容 |
| `genre` | Array(String) | 类型/流派 |
| `notable_work` | String | 代表作 |
| `present_in_work` | String | 出现在作品中 |
| `series` | String | 系列 |
| `based_on` | String | 基于...改编 |
| `original_broadcaster` | String | 原始播出平台 |
| `publisher` | Array(String) | 出版商 |
| `author` | String | 作者 |
| `director` | Array(String) | 导演 |
| `composer` | Array(String) | 作曲 |
| `screenwriter` | Array(String) | 编剧 |
| `cast_member` | Array(String) | 演员阵容 |
| `narrative_location` | String | 叙事地点 |
| `set_in_period` | String | 设定时期 |
| `contributor_to_the_creative_work_or_subject` | String | 创作贡献者 |
| `copyright_license` | String | 版权许可 |
| `distribution_format` | String | 发行格式 |
| `intended_public` | Array(String) | 目标受众 |

---

## 十五、时间戳 (10 列)

| 字段 | 类型 | 说明 |
|---|---|---|
| `create_time` | DateTime | 记录创建时间 |
| `update_time` | DateTime | 记录更新时间 |
| `inception` | Int64 | 成立/开始时间 |
| `register_time` | Int64 | 注册时间 |
| `dissolved_abolished_or_demolished` | Int64 | 解散/废除/拆除时间 |
| `date_of_official_opening` | Int64 | 正式开放日期 |
| `date_of_official_closure` | Int64 | 正式关闭日期 |
| `date_of_disappearance` | Array(Int64) | 消失日期 |
| `significant_event.significant_event_content` | Array(String) | 重要事件 — 内容 |
| `significant_event.significant_event_time` | Array(Int64) | 重要事件 — 时间 |

---

## 十六、质控与枚举 (4 列)

| 字段 | 类型 | 说明 |
|---|---|---|
| `confidence` | Enum8 | 置信度（极低/低/中/高/极高） |
| `security_level` | Enum8 | 安全级别（无/低/中/高） |
| `vital_node` | Int32 | 重要节点标记 |
| `has_quality` | Array(String) | 质量属性 |

---

## 十七、标签与分类 (6 列)

| 字段 | 类型 | 说明 |
|---|---|---|
| `labels` | Array(String) | 标签 |
| `main_subject` | Array(String) | 主要主题 |
| `stats_attr.key` | Array(String) | 统计属性键 |
| `stats_attr.value` | Array(String) | 统计属性值 |
| `stats_attr.vtype` | Array(String) | 统计属性值类型 |

---

## 十八、文本描述 (3 列)

| 字段 | 类型 | 说明 |
|---|---|---|
| `text` | String | 文本内容 |
| `abstract` | String | 摘要 |
| `description` | String | 描述 |

---

## 十九、杂项 (12 列)

| 字段 | 类型 | 说明 |
|---|---|---|
| `shape` | String | 形状 |
| `geoshape` | String | 地理形状 |
| `operating_system` | String | 操作系统 |
| `fabrication_method` | String | 制造方法 |
| `material_used` | String | 使用材料 |
| `source_of_energy` | String | 能源 |
| `instrumentation` | Array(String) | 仪器设备 |
| `brand` | String | 品牌 |
| `product_or_material_produced` | Array(String) | 生产产品/材料 |
| `quantity` | Int32 | 数量 |
| `subject_count` | Int32 | 主题数量 |
| `follow_num` | Int32 | 关注数 |

---

## 概要统计

| 类别 | 列数 | 占比 |
|---|---|---|
| 物理尺寸与测量 | 33 | 9.5% |
| 军事 | 30 | 8.7% |
| 媒体与作品 | 26 | 7.5% |
| 政治与政府 | 24 | 6.9% |
| 组织信息 | 24 | 6.9% |
| 地理位置 | 22 | 6.4% |
| 经济与金融 | 16 | 4.6% |
| 职业与职位 | 16 | 4.6% |
| 联系方式 | 14 | 4.0% |
| 人口统计学 | 14 | 4.0% |
| 基础设施与交通 | 14 | 4.0% |
| 杂项 | 12 | 3.5% |
| 教育背景 | 10 | 2.9% |
| 时间戳 | 10 | 2.9% |
| 家庭与亲属关系 | 8 | 2.3% |
| 基础标识与元信息 | 7 | 2.0% |
| 标签与分类 | 6 | 1.7% |
| 质控与枚举 | 4 | 1.2% |
| 文本描述 | 3 | 0.9% |

> 注：部分字段出现多个类别中（如 `place_of_birth` 同时出现在地理位置和人口统计学），实际唯一边际计数略小于分类之和。此表实体类型覆盖面极广，从人物、组织、地点到军事装备、媒体作品均有涉及。

---

## 附：实体类型分布

| type | 行数 | 占比 |
|---|---|---|
| `geographic_entity` | 3,984,491 | 34.8% |
| `human` | 3,720,754 | 32.5% |
| `administrative` | 2,005,622 | 17.5% |
| `organization` | 920,330 | 8.0% |
| `weapon` | 43,128 | 0.4% |
| `product` | 1,781 | < 0.1% |
| `cyber_user` | 1,080 | < 0.1% |
| `other_entity` | 148 | < 0.1% |
| `work` | 3 | < 0.1% |
| `''` (空值) | 2 | < 0.1% |
| **合计** | **~11,457,339** | **100%** |

> 地理实体（`geographic_entity`）占比最高，其次为人物（`human`）和行政区划（`administrative`），三者合计占总量约 85%。

---

## 二十、Human 类型字段填充率分析（2026-05-13）

> 分析基于 `type='human'` 的 3,720,754 行记录，统计每列非空/非默认值的比例。
>
> **注意**：数值列（Int/Float）只要非 NULL 即算"有数据"。ClickHouse 中非 Nullable 的数值列默认值为 0，
> 因此所有数值列均显示 **100%** 填充。真正有区分度的是 String 和 Array 列。

### 20.1 概览

| 指标 | 值 |
|---|---|
| `type='human'` 行数 | 3,720,754 |
| 总列数 | 346 |
| 有数据列 | 171（49.4%） |
| 完全为空列 | 175（50.6%） |

### 20.2 高填充列（String/Array, fill ≥ 10%）

这些是查询 human 实体时**最常用**的列：

| 填充率 | 非空行数 | 字段 | 类型 | 说明 |
|---|---|---|---|---|
| 96.0% | 3,570,439 | `sex_or_gender` | String | 性别 |
| 87.2% | 3,245,289 | `occupation` | Array(String) | 职业 |
| 75.9% | 2,824,145 | `text` | String | 描述文本 |
| 72.4% | 2,694,104 | `country_of_citizenship` | Array(String) | 国籍 |
| 57.9% | 2,154,386 | `place_of_birth` | Array(String) | 出生地 |
| 25.2% | 937,302 | `nonnative_names` | Array(String) | 非原生语言名称 |
| 23.3% | 867,255 | `education_experience.*` (4列) | Array | 教育经历 |
| 22.8% | 849,200 | `image` | Array(String) | 图片 URL |
| 22.0% | 817,603 | `place_of_death` | String | 死亡地点 |
| 21.8% | 810,293 | `school` | String | 学校 |
| 20.5% | 763,098 | `position_experience.*` (4列) | Array | 任职经历 |
| 12.2% | 453,519 | `position_held` | Array(String) | 曾担任职位 |
| 11.3% | 420,883 | `award_received` | Array(String) | 获奖 |

### 20.3 中填充列（String/Array, 1% ≤ fill < 10%）

| 填充率 | 非空行数 | 字段 | 类型 |
|---|---|---|---|
| 8.8% | 327,596 | `department_or_company` | String |
| 8.7% | 322,996 | `member_of_political_party` | Array(String) |
| 5.2% | 195,178 | `abstract` | String |
| 5.0% | 185,946 | `work_location` | Array(String) |
| 4.6% | 171,647 | `father` | String |
| 4.1% | 151,987 | `religion` | Array(String) |
| 3.9% | 146,123 | `member_of` | Array(String) |
| 3.9% | 144,674 | `child` | Array(String) |
| 3.8% | 141,833 | `spouse` | Array(String) |
| 3.6% | 133,744 | `native_language` | String |
| 3.4% | 127,333 | `personal_website_account` | Array(String) |
| 3.0% | 113,094 | `sibling` | Array(String) |
| 3.0% | 111,368 | `twitter_username` | Array(String) |
| 2.6% | 96,491 | `official_website` | Array(String) |
| 2.4% | 90,966 | `military_rank` | Array(String) |
| 2.4% | 89,670 | `cause_of_death` | String |
| 2.2% | 82,812 | `aliases` | Array(String) |
| 2.1% | 77,717 | `mother` | String |
| 2.0% | 75,283 | `ethnic_group` | Array(String) |
| 2.0% | 72,818 | `hometown` | Array(String) |
| 1.9% | 72,310 | `manner_of_death` | String |
| 1.9% | 71,453 | `military_branch` | Array(String) |
| 1.9% | 70,094 | `academic_degree` | Array(String) |
| 1.4% | 53,860 | `facebook_id` | Array(String) |
| 0.8% | 28,058 | `pseudonym` | Array(String) |
| 0.2% | 6,514 | `unmarried_partner` | String |
| 0.1% | 1,983 | `political_leaning` | String |

### 20.4 低填充列（String/Array, fill < 0.1%）

数据极少，但某些场景有用：

`labels` (1,088), `short_name` (878), `social_media_account` (714), `email` (656),
`academic_major` (635), `phone_number` (565), `ancestral_home` (555),
`residence` (522), `date_of_disappearance` (522), `political_ideology` (309),
`country` (161), `telephone` (148), `headquarters_location` (115),
`education_background` (73), `professional_division` (70),
`political_faction` (44), `fax` (44), `bank_account` (33),
`armament.*` (21), `address` (18), `postal_code` (9),
`use` (8), `stats_attr.*` (7), `capital.*` (4),
`medias.*` (3), `call_sign` (2), `employee_number.*` (1),
`vessel_class` (1), `notes.*` (1)

### 20.5 完全为空的列（175 列）

对 human 类型完全无数据的列，多属武器/军事/组织/行政区划专有字段：

```
legal_form, industry, population.*, gdp.*, member_count.*,
continent, located_in_or_next_to_body_of_water, gini_coefficient.*,
local_dialing_code, location_of_creation, total_produced.*,
cost.*, length.length_unit, width.width_unit, mass.mass_unit,
diameter.diameter_unit, wingspan.wingspan_unit, pennant_number,
register_loc, former_name, title, political_status, owned_by,
runway.*, altitude.altitude_unit, participated_in_wars, garrison,
commanded_by, geoshape, street_address, used_by,
hull_length.hull_length_unit, hull_width.hull_width_unit,
draft.draft_unit, crew_member, cruise_speed.cruise_speed_unit,
standard_displacement.standard_displacement_unit,
full_loaded_displacement.full_loaded_displacement_unit,
power_system, firing_range.firing_range_unit, service_city,
area.*, arm_of_the_services, operator, built_by,
combat_radius.combat_radius_unit, battle_group, subordinate_fleet,
flight_deck_length.flight_deck_length_unit, hangar_width.hangar_width_unit,
home_port, hangar_length.hangar_length_unit,
angled_deck_length.angled_deck_length_unit,
flight_deck_width.flight_deck_width_unit,
detection_distance.detection_distance_unit,
length_between_perpendiculars.length_between_perpendiculars_unit,
close_in_weapon, hangar_height.hangar_height_unit,
cost.cost_unit, total_produced.total_produced_unit,
warship_captain.*, patron_num.*, caliber.*,
significant_event.*, area.area_time, gdp.gdp_unit,
population.population_unit, member_count.member_count_unit,
employee, deputy_commanded_by, chief_of_staff, subsidiary,
parent_organization, countries_covered_by_jurisdiction,
place, secretary_general, founded_by,
contains_administrative_territorial_entity, shares_border_with,
executive_branch, driving_side, time_zone, legislature,
national_anthem, currency, country_calling_code,
emergency_phone_number, basic_form_of_government,
highest_judicial_authority, public_holiday, top_level_domain,
official_language, flag, head_of_state.*, head_of_government.*,
named_after, located_in_the_administrative_territorial_entity,
twin_town, logo_image, station_code, owner,
director_of_the_organization, leader, list_of_monuments,
product_or_material_produced, language_of_work, main_subject,
contains_settlement, location_of_formation, genre,
contact_phone_number, editor, official_symbol,
chief_executive_officer, operating_area, planning,
business_division, distribution_format, notable_work,
material_used, members_have_occupation, art_director,
aerodrome_reference_point, price.price_unit, copyright_license,
present_in_work, original_broadcaster, business_model, shape,
intended_public, official_app, chief_operating_officer,
commissioned_by, corporate_officer, has_quality, operating_system,
fabrication_method, developer, series, based_on, cast_member,
set_in_period, director, screenwriter,
contributor_to_the_creative_work_or_subject, narrative_location,
composer, duration.duration_unit, source_of_energy,
instrumentation, author, publisher, volume.volume_unit,
transmitted_signal_type, brand
```

### 20.6 对查询的指导意义

1. **优先使用高填充列**：`name` + `type` 永远是 WHERE 条件；`occupation`、`country_of_citizenship`、`place_of_birth` 查询命中率高
2. **大宽表中只有约一半列对 human 有价值**，另一半（武器/组织专属列）可完全忽略
3. **教育经历和任职经历**以嵌套数组结构存储，需用 `ARRAY JOIN` 展开
4. **数值列（如 height、weight 等）默认填充 0**，实际有意义的记录只有 `height.height_unit` (4.3%)、`weight.weight_unit` (3.1%) 等配套字段可以佐证
5. 175 个空列对 human 查询可安全忽略
