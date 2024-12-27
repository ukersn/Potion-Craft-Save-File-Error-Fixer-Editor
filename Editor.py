import base64
import json
import os
import sys
from datetime import datetime

xor_key = "a^19uh%47x71e%sd"
def xor_crypt(data, key):
    encrypted = bytearray()
    key_length = len(key)
    for i, byte in enumerate(data):
        encrypted.append(byte ^ ord(key[i % key_length]))
    return bytes(encrypted)


def get_nested_value(data, path):
    keys = path.split('.')
    for key in keys:
        if isinstance(data, dict):
            data = data.get(key)
        else:
            return None
    return data


def set_nested_value(data, path, value):
    keys = path.split('.')
    for key in keys[:-1]:
        if key not in data:
            data[key] = {}
        data = data[key]
    data[keys[-1]] = value


def process_save_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
        if len(lines) < 2:
            raise ValueError("读取失败，文件格式不正确，这可能不是一个存档文件？(Read failed, incorrect file format. Is this possibly not a save file?)")

        base64_content1 = lines[0].strip()
        base64_content2 = lines[1].strip()


    # 处理两段内容
    decoded_content1 = base64.b64decode(base64_content1)
    decrypted_content1 = xor_crypt(decoded_content1, xor_key)
    json_content1 = json.loads(decrypted_content1.decode('utf-8'))

    decoded_content2 = base64.b64decode(base64_content2)
    decrypted_content2 = xor_crypt(decoded_content2, xor_key)
    json_content2 = json.loads(decrypted_content2.decode('utf-8'))

    return json_content1, json_content2, base64_content1, base64_content2


def save_modified_content(file_path, json_content1, json_content2):


    # 创建备份
    backup_time = datetime.now().strftime("%Y%m%d%H%M%S")
    file_name = os.path.basename(file_path)
    file_name_without_ext = os.path.splitext(file_name)[0]
    backup_file_name = f"{file_name_without_ext}.backup{backup_time}"
    backup_path = os.path.join(os.getcwd(), backup_file_name)

    # 复制原文件作为备份
    import shutil
    shutil.copy2(file_path, backup_path)

    print(f"原存档文件已备份为: {backup_file_name} (Original save file backed up as: {backup_file_name})")


    # 重新加密内容
    encrypted_content1 = xor_crypt(json.dumps(json_content1, separators=(',', ':')).encode('utf-8'), xor_key)
    encrypted_content2 = xor_crypt(json.dumps(json_content2, separators=(',', ':')).encode('utf-8'), xor_key)

    base64_content1 = base64.b64encode(encrypted_content1).decode('utf-8')
    base64_content2 = base64.b64encode(encrypted_content2).decode('utf-8')

    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(base64_content1 + '\n' + base64_content2)


def main():
    file_path = ""
    if len(sys.argv) == 1:
        while not os.path.isfile(find_file_with_similar_name(file_path)):
            file_path = input("请输入存档文件路径 (Enter the save file path): ").strip().strip('"')
            file_path = find_file_with_similar_name(file_path).strip('"')
            if not os.path.isfile(find_file_with_similar_name(file_path)):
                print("文件不存在，请重新输入。(File does not exist, please enter again.)")
    else:
        file_path = find_file_with_similar_name(sys.argv[1]).strip('"')



    fix_choice = input(
        "你是想修复这个游戏存档么？(如果是的话输入Y，否则进入存档字段的修改模式) Do you want to fix this game save? (Enter Y to fix, or enter any other key to modify save fields): ").strip().lower()
    if fix_choice == 'y':
        fixMode1(file_path)
        return

    try:
        json_content1, json_content2, base64_content1, base64_content2 = process_save_file(file_path)

        while True:
            command = input("输入修改指令 (格式: 字段路径 新值) 或 'q' 退出: (Enter modification command (format: field path new value) or 'q' to quit: )").strip()
            if command.lower() == 'q':
                break

            parts = command.split(maxsplit=1)
            if len(parts) != 2:
                print("无效的输入格式。请使用 '字段路径 新值' 的格式。(Invalid input format. Please use the format 'field_path new_value'.)")
                continue

            path, value = parts
            try:
                # 尝试将值转换为数字或布尔值，如果失败则保持为字符串
                try:
                    value = json.loads(value)
                except json.JSONDecodeError:
                    pass  # 保持为字符串

                # 确定修改哪一部分内容
                if get_nested_value(json_content1, path) is not None:
                    set_nested_value(json_content1, path, value)
                    print(f"已修改第一段内容: {path} = {value} (Modified first section content: {path} = {value})")
                elif get_nested_value(json_content2, path) is not None:
                    set_nested_value(json_content2, path, value)
                    print(f"已修改第二段内容: {path} = {value} (Modified second section content: {path} = {value})")
                else:
                    print(f"未找到字段: {path} (Field not found: {path})")
            except Exception as e:
                print(f"修改失败: {str(e)} (Modification failed: {str(e)})")

        # 保存修改后的内容
        save_modified_content(file_path, json_content1, json_content2)
        print("修改已保存。(Modifications saved.)")

    except Exception as e:
        print(f"发生错误: {str(e)} (Error occurred: {str(e)})")

def fixMode1(file_path):
    try:
        json_content1, json_content2, _, _ = process_save_file(file_path)


        #处理因为左右键同时点击导航按钮而切到未解锁房间的存档
        if 'savePool' in json_content1:
            json_content2['savePool'] = 21
            print("已重置存档保存标记 savePool = 1 (Reset save file marker: savePool = 1)")
        else:
            print("未找到字段: savePool (Field not found: savePool)")
            return

        #处理因为左右键同时点击导航按钮而切到未解锁房间的存档
        if 'currentRoom' in json_content2:
            json_content2['currentRoom'] = 1
            print("已重置玩家当前房间到实验室: currentRoom = 1 (Reset player's current room to laboratory: currentRoom = 1)")
        else:
            print("未找到字段: currentRoom (Field not found: currentRoom)")
            return

        #处理物品卡到未解锁房间的存档
        # Step 1: Read unlockedRooms field
        unlocked_rooms = get_nested_value(json_content2, 'unlockedRooms')
        if not unlocked_rooms:
            print("未找到 unlockedRooms 字段 (unlockedRooms field not found)")
            return

        # Step 2 & 3: Process itemsFromInventory
        items_from_inventory = get_nested_value(json_content2, 'itemsFromInventory')
        if not items_from_inventory:
            print("未找到 itemsFromInventory 字段 (itemsFromInventory field not found)")
            return
        fixed_count = 0 #BuildZone被篡改的物品计数
        modified_count = 0 #被卡到未解锁房间的物品计数
        for item in items_from_inventory:
            position = item.get('position', {})
            x = position.get('x', 0)
            y = position.get('y', 0)

            should_modify = False

            # Condition set a
            if 8 not in unlocked_rooms and x < -14 and y < -7:
                should_modify = True
            elif 7 not in unlocked_rooms and x > 39 and y < -7:
                should_modify = True
            elif 6 not in unlocked_rooms and x > 14 and y < -7:
                should_modify = True
            elif 5 not in unlocked_rooms and x > 39 and y > -7:
                should_modify = True

            # Condition set b
            if y > 9 and x < -14:
                should_modify = True
            elif y > 9 and x > 14:
                should_modify = True
            elif x < -40 or x > 65:
                should_modify = True
            elif y < -21 or y > 23:
                should_modify = True

            if should_modify:
                item['position'] = {'x': -2, 'y': 10}
                modified_count += 1
                print(f"物品位置已修改 (Item position modified): typeName = {item.get('typeName')}")

            data = item.get('data', '')
            modified = False
            if '"buildZoneRoomIndex\":4' in data and 'BuildableItem Foreground Chests' in data:
                data = data.replace('BuildableItem Foreground Chests', 'Background Shelves')
                modified = True
            elif '"buildZoneRoomIndex\":4' in data and  'BuildableItem Foreground Shelves' in data:
                data = data.replace('BuildableItem Foreground Shelves', 'Foreground Chests')
                modified = True

            if modified:
                item['data'] = data
                fixed_count += 1
                print(f"物品BuildZone已修复 (Item BuildZone fixed): inventoryItemName = {item.get('inventoryItemName')}")

        if modified_count > 0:
            print(f"共修改了 {modified_count} 个物品的位置 (Modified positions of {modified_count} items)")
        else:
            print("没有需要修改的物品 (No items needed modification)")

        if fixed_count > 0:
            print(f"共修复了 {fixed_count} 个物品的BuildZone (Fixed BuildZone of {fixed_count} items in total)")
        else:
            print("没有需要修复BuildZone的物品 (No items needed BuildZone fixing)")
        print("存档错误尝试修复完成。(Save file error fix attempt completed.)")

        # 保存修改后的内容
        save_modified_content(file_path, json_content1, json_content2)
        print("修改已保存。(Modifications saved.)")

    except Exception as e:
        print(f"发生错误: {str(e)} (Error occurred: {str(e)})")

def find_file_with_similar_name(file_path):

    file_path=file_path.strip('"')
    if file_path.strip()=="":
        return ""

    directory, filename = os.path.split(file_path)
    for file in os.listdir(directory):
        if file.replace("—", "-") == filename.replace("—", "-"):
            return os.path.join(directory, file)
    return None
def decode_and_save(file_path):
    try:
        json_content1, json_content2, _, _ = process_save_file(file_path)

        # 合并两个 JSON 内容
        combined_json = {
            "content1": json_content1,
            "content2": json_content2
        }

        # 创建输出文件名
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        output_file = f"{base_name}_decoded.json"

        # 保存解码后的 JSON
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(combined_json, f, ensure_ascii=False, indent=2)

        print(f"解码完成。保存到文件: {output_file} (Decoding completed. Saved to file: {output_file})")
    except Exception as e:
        print(f"解码过程中发生错误: {str(e)} (Error occurred during decoding: {str(e)})")
def encode_and_save(json_file_path):
    try:
        # 读取JSON文件
        with open(json_file_path, 'r', encoding='utf-8') as f:
            combined_json = json.load(f)

        # 分离两部分内容
        json_content1 = combined_json["content1"]
        json_content2 = combined_json["content2"]

        # 重新加密内容
        encrypted_content1 = xor_crypt(json.dumps(json_content1, separators=(',', ':')).encode('utf-8'), xor_key)
        encrypted_content2 = xor_crypt(json.dumps(json_content2, separators=(',', ':')).encode('utf-8'), xor_key)

        base64_content1 = base64.b64encode(encrypted_content1).decode('utf-8')
        base64_content2 = base64.b64encode(encrypted_content2).decode('utf-8')

        # 创建输出文件名
        base_name = os.path.splitext(os.path.basename(json_file_path))[0]
        output_file = f"{base_name}_encoded.pcsave"

        # 保存加密后的内容
        with open(output_file, 'w', encoding='utf-8') as file:
            file.write(base64_content1 + '\n' + base64_content2)

        print(f"编码完成。保存到文件: {output_file} (Encoding completed. Saved to file: {output_file})")
    except Exception as e:
        print(f"编码过程中发生错误: {str(e)} (Error occurred during encoding: {str(e)})")



if __name__ == "__main__":
    if len(sys.argv) == 2:
        fixMode1(find_file_with_similar_name(sys.argv[1].strip('"')))
    elif len(sys.argv) == 3 and sys.argv[2] == "--decode":
        decode_and_save(find_file_with_similar_name(sys.argv[1].strip('"')))
    elif len(sys.argv) == 3 and sys.argv[2] == "--encode":
        encode_and_save(find_file_with_similar_name(sys.argv[1].strip('"')))
    else:
        main()
    print("\n按任意键继续...(Press any key to continue...)")
    input()


"""我靠，那个坏档，我终于是有点头绪了。

有这些BuildZone，用来放家具的东西：
一个房间被分为了前后两个建筑区域(就像图片的图层)
Foreground Chests   房间的前景区域，比如桌子、床之类的玩意。
Background Shelves  房间的背景区域，比如架子，奖杯这些东西。

在同一个区域里的东西不能互相碰撞，也就是床跟桌子没办法叠在一起放，但前景跟背景区域就不冲突，也就是意味着像各种架子和奖杯什么的可以显示在桌子、床这些前景建筑的后面。
如图所示：



然后我检查那些坏档的时候，发现像床什么的物品，有的data数据的BuildZone变成了
BuildableItem Foreground Shelves
BuildableItem Foreground Chests

这两个另类的玩意，这两个玩意我找遍了我的存档都没见过有东西使用这个BuildZone。  所以怀疑是保存的时候发生什么，使得一些物品的BuildZone转变成那两个另类的玩意。

理论上我现在要做的就是找出存档中这些被转变成这两个另类的BuildZone的物品，区分并修改它是放在正常的前景还是背景，然后保存。就可以了。 不过还有一些其他参数我有点看不懂，就先这样写试试

值得一提的是，所有这种错误BuildZone的变化都发生在卧室。不知道游戏开发者又在搞什么东西



尝试后：
BuildableItem Foreground Chests -> Background Shelves
BuildableItem Foreground Shelves -> Foreground Chests
仅在卧室有用，放其他地方要报错的，因为其他地方真的有这个BuildZone
"""