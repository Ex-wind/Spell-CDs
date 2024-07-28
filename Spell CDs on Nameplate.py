import re
from datetime import datetime

log_pattern = re.compile(
    r'(\d{1,2}/\d{1,2}/\d{4}) (\d{2}:\d{2}:\d{2}\.\d{4}).*?Creature-\d+-\d+-\d+-\d+-(\d+)-(\w+),"(.*?)".*?'
)
spell_cast_start_pattern = re.compile(
    r'(\d{1,2}/\d{1,2}/\d{4}) (\d{2}:\d{2}:\d{2}\.\d{4})\s+SPELL_CAST_START,Creature-\d+-\d+-\d+-\d+-(\d+)-(\w+),"(.*?)",.*?,.*?,(\d+),"(.*?)",.*?'
)
spell_cast_success_pattern = re.compile(
    r'(\d{1,2}/\d{1,2}/\d{4}) (\d{2}:\d{2}:\d{2}\.\d{4})\s+SPELL_CAST_SUCCESS,Creature-\d+-\d+-\d+-\d+-(\d+)-(\w+),"(.*?)",.*?,.*?,(\d+),"(.*?)",.*?'
)

# 要处理的法术ID / Spell IDs to be processed
target_spell_ids = [
"428202",
]

# 存储怪物进入战斗的时间 / Store the time when the creature enters combat
combat_start_time = {}
# 存储上一次法术施放成功的时间 / Store the time when the spell was last successfully cast
last_cast_success_time = {spell_id: {} for spell_id in target_spell_ids}
# 存储每个法术的冷却时间 / Store the cooldown times for each spell
cooldowns = {spell_id: [] for spell_id in target_spell_ids}
# 存储每个怪物的首次施放时间 / Store the first cast time for each creature
first_cast_time = {spell_id: {} for spell_id in target_spell_ids}
first_cast_info = {spell_id: {} for spell_id in target_spell_ids}  # 用于存储首次施放信息 / Used to store the first cast information

# 在这修改读取的战斗日志路径 / Modify the path of the combat log to be read here
with open('combatlog.txt', 'r', encoding='utf-8') as file:
    lines = file.readlines()

# 获取每个怪物进入战斗的时间 / Get the time when each creature enters combat
for line in lines:
    match = log_pattern.match(line)
    if match:
        date_str, time_str, creature_id, guid, creature_name = match.groups()
        timestamp = datetime.strptime(f"{date_str} {time_str}", "%m/%d/%Y %H:%M:%S.%f")
        full_guid = f"{creature_id}-{guid}"
        if full_guid not in combat_start_time:
            combat_start_time[full_guid] = timestamp

# 获取SPELL_CAST_SUCCESS和SPELL_CAST_START并计算冷却时间 / Get SPELL_CAST_SUCCESS and SPELL_CAST_START and calculate cooldown
for line in lines:
    # SPELL_CAST_SUCCESS 
    match = spell_cast_success_pattern.match(line)
    if match:
        date_str, time_str, creature_id, guid, creature_name, spell_id, spell_name = match.groups()
        if spell_id in target_spell_ids:
            timestamp = datetime.strptime(f"{date_str} {time_str}", "%m/%d/%Y %H:%M:%S.%f")
            full_guid = f"{creature_id}-{guid}"
            last_cast_success_time[spell_id][full_guid] = timestamp

    # SPELL_CAST_START 
    match = spell_cast_start_pattern.match(line)
    if match:
        date_str, time_str, creature_id, guid, creature_name, spell_id, spell_name = match.groups()
        if spell_id in target_spell_ids:
            timestamp = datetime.strptime(f"{date_str} {time_str}", "%m/%d/%Y %H:%M:%S.%f")
            full_guid = f"{creature_id}-{guid}"
            if full_guid not in first_cast_time[spell_id]:
                first_cast_time[spell_id][full_guid] = timestamp
                first_cast_info[spell_id][full_guid] = (creature_name, spell_name)
            if full_guid in last_cast_success_time[spell_id]:
                previous_timestamp = last_cast_success_time[spell_id][full_guid]
                cooldown = (timestamp - previous_timestamp).total_seconds()
                cooldowns[spell_id].append((cooldown, creature_id, creature_name, spell_name, full_guid))
                del last_cast_success_time[spell_id][full_guid]  

# 存储没有冷却时间的数据 / Store data with no cooldown times
no_cooldown_data = []

# 输出格式 / Output format
for spell_id in target_spell_ids:
    if cooldowns[spell_id]:
        min_cooldown_data = min(cooldowns[spell_id], key=lambda x: x[0])
        min_cooldown, creature_id, creature_name, spell_name, full_guid = min_cooldown_data
    
        print("{")
        print(f'["tank"] = true,')
        print(f'["active"] = true,')
        print(f'["intduration"] = {min_cooldown:.1f},')
        print(f'["duration"] = {min_cooldown:.1f},')
        print(f'["spelltrigger"] = "0",')
        print(f'["overwrite"] = 0,')
        print(f'["casttype"] = 2,')
        print(f'["offsetnum"] = "",')
        print(f'["npcIDoffset"] = "",')
        print(f'["mdps"] = true,')
        print(f'["desynch"] = 0,')
        
        # 计算进入战斗后施放法术的时间差 / Calculate the time difference of casting spells after entering combat
        if full_guid in combat_start_time:
            combat_start = combat_start_time[full_guid]
            first_cast = first_cast_time[spell_id][full_guid]
            combat_duration = (first_cast - combat_start).total_seconds()
            # 判定 combat_duration 最高为 60 / Ensure combat_duration does not exceed 60
            if combat_duration > 60:
                combat_duration = 60
            print(f'["combattimer"] = {combat_duration:.1f},')
        else:
            print(f'["combattimer"] = 10,')  # 默认值为10 / Default value is 10

        print(f'["hideafter"] = 10,')
        print(f'["npcID"] = "{creature_id}",')
        print(f'["desc"] = "{creature_name} - {spell_name}",')
        print(f'["loop"] = false,')
        print(f'["progressive"] = "0",')
        print(f'["spelltimer"] = "0",')
        print(f'["repeating"] = false,')
        print(f'["rdps"] = true,')
        print(f'["oncombat"] = true,')
        print(f'["heal"] = true,')
        print(f'["spellID"] = {spell_id},')
        print("},")
    else:
        if first_cast_time[spell_id]:
            example_guid = list(first_cast_time[spell_id].keys())[0]
            creature_name, spell_name = first_cast_info[spell_id][example_guid]
            creature_id = example_guid.split('-')[0]
            print("{")
            print(f'["tank"] = true,')
            print(f'["active"] = true,')
            print(f'["intduration"] = "",')
            print(f'["duration"] = "",')
            print(f'["spelltrigger"] = "0",')
            print(f'["overwrite"] = 0,')
            print(f'["casttype"] = 2,')
            print(f'["offsetnum"] = "",')
            print(f'["npcIDoffset"] = "",')
            print(f'["mdps"] = true,')
            print(f'["desynch"] = 0,')
            if example_guid in combat_start_time:
                combat_start = combat_start_time[example_guid]
                first_cast = first_cast_time[spell_id][example_guid]
                combat_duration = (first_cast - combat_start).total_seconds()
                # 判定 combat_duration 最高为 60 / Ensure combat_duration does not exceed 60
                if combat_duration > 60:
                    combat_duration = 60
                print(f'["combattimer"] = {combat_duration:.1f},')
            else:
                print(f'["combattimer"] = 10,')  # 默认值为10 / Default value is 10
            print(f'["hideafter"] = 10,')
            print(f'["npcID"] = "{creature_id}",')
            print(f'["desc"] = "{creature_name} - {spell_name}",')
            print(f'["loop"] = false,')
            print(f'["progressive"] = "0",')
            print(f'["spelltimer"] = "0",')
            print(f'["repeating"] = false,')
            print(f'["rdps"] = true,')
            print(f'["oncombat"] = true,')
            print(f'["heal"] = true,')
            print(f'["spellID"] = {spell_id},')
            print("},")
        else:
            no_cooldown_data.append(f"No cooldowns detected for spell ID: {spell_id}")

# 输出没有冷却时间的数据 / Output data with no cooldown times
for message in no_cooldown_data:
    print(message)
