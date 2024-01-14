import os
import time
import re
import cv2
from datetime import datetime

import subprocess
import numpy as np
import base64

import adb
import settings
import openCV

def Read_file(): # 讀檔
    global settings_path
    global int_vars
    global string_vars
    global gTemp
    print("-----------------------------------------------------")
    print("Start to read settings by {}".format(settings_path))
    print("-----------------------------------------------------")

    for line in open(settings_path,encoding = "gb18030",errors = "ignore"):
        # Get rid of #
        if(len(re.findall("#",line)) > 0):
            line = re.findall("^(.*)#",line)[0]
        # print(line)
        # Set strings
        for string_var in string_vars:
            k = re.findall("^ *{} *= *\"(.+)\"".format(string_var),line)
            if(len(k)>0):
                gTemp = k[0]
                print("set {} : {}".format(string_var,gTemp))
                exec("settings.{} = gTemp".format(string_var),globals())
                #print("test : "+string_var) #存等號左邊
                #print("test : "+gTemp) #存等號右邊
        # Set ints
        for int_var in int_vars:
            k = re.findall("^ *{} *= *(.+)".format(int_var),line)
            if(len(k)>0):
                gTemp = int(k[0])
                print("set {} : {}".format(int_var,str(gTemp)))
                exec("settings.{} = gTemp".format(int_var),globals())

    print("-----------------------------------------------------")
    print("Finished read settings by {}".format(settings_path))
    print("-----------------------------------------------------")

def Set_Target_Time( num ): # 設定刷關時間
    global gHour
    global gMins
    global gCount
    current_Date_And_Time = datetime.now()
    if ( num == 0 ):
        gHour = int(current_Date_And_Time.strftime("%H"))
        gMins = int(current_Date_And_Time.strftime("%M"))
        Add_Target_Time( 0 )
    else:
        if ( settings.Use_current_time != 0 ):
            gHour = int(current_Date_And_Time.strftime("%H"))
            gMins = int(current_Date_And_Time.strftime("%M")) + 1
            print( "gHour: " + str(gHour) + " gMins: " + str(gMins) )
        else:
            gHour = settings.target_hour
            gMins = settings.target_mins

    if ( settings.Change_progress != 0 ):
        gCount = int(settings.Change_progress)

def Add_Target_Time( num ): # 設定下一次刷關時間
    global gHour
    global gMins
    global gCount
    if ( num == 0 ):
        gMins = int(gMins) + 50
    elif ( num == 1 ):
        gMins = int(gMins) + 50
        gCount = int(gCount) + 1
    elif ( num == 2 ):
        gHour = int(gHour) + 1
        gCount = int(gCount) + 1

    if ( gMins > 59 ):
        gMins = int(gMins) - 60
        gHour = int(gHour) + 1
    if ( gHour > 23 ):
        gHour = int(gHour) - 24

def Time_To_start(): # 是否達到目標時間
    global gHour
    global gMins
    current_Date_And_Time = datetime.now()
    now_Hour = int(current_Date_And_Time.strftime("%H"))
    now_Mins = int(current_Date_And_Time.strftime("%M"))

    if ( gHour == now_Hour and gMins == now_Mins ):
        return True

    return False

def afk():
    global gError
    loc = None
    loc = openCV.sub_match_template( r"template\start\list.png", 0.01, False )
    if ( loc == None ):
        loc = openCV.sub_match_template( r"template\start\home.png", 0.01, False )
    if ( loc == None ):
        loc = openCV.sub_match_template( r"template\start\main_ad_close.png", 0.01, False )
    if ( loc == None ):
        loc = openCV.sub_match_template( r"template\quest\ad_confirm.png", 0.01, False )
    if ( loc == None ):
        loc = openCV.sub_match_template( r"template\start\emulator_ad_close.png", 0.01, False )
    if ( loc == None ):
        loc = openCV.sub_match_template( r"template\start\open_marvel.png", 0.01, False )
    if ( loc == None ):
        loc = openCV.sub_match_template( r"template\start\close_app.png", 0.01, False )\

    if ( loc != None ):
        adb.click( loc )
    else:
        adb.screenshot( "temp_screenshot\Error_afk_unexcepted_pic_" + str(gError) + "_.png" )
        gError = int(gError) + 1

def Start_Quest( topic, team, num, quick_pass ): # 開始刷關
    global gError
    global gAppCrash
    global gMatl_Full
    in_main_page = False  # 是否在 "主頁面"
    in_epic_quest = False # 是否在 "史詩任務" 頁面
    in_msn_prep = False   # 是否在 "任務準備" 頁面
    check_team = False    # 是否完成點擊 "隊伍"
    have_ad = False       # 刷關前是否完有廣告
    clear_quest = False   # 是否刷關完成
    wait_farm = False     # 等待刷關時間
    if_end = False        # 是否回到遊戲主頁面
    error_occur = False   # 非預期畫面出現
    error_num = 0
    totally_finished = False # 檢查是否正常的刷關完成(無閃退)
    wait_app_loading = False

    global last_topic
    global last_team
    global last_num
    global last_quick_pass
    last_topic = topic
    last_team = team
    last_num = num
    last_quick_pass = quick_pass

    while ( True ):
        loc = None

        if ( not in_main_page): # 是否在"主頁面"                     error:1
            if ( have_ad ): # 關閉能量增幅組合包 點擊"確定" 或是 點擊"廣告關閉確定"
                loc = openCV.sub_match_template( r"template\quest\ad_confirm.png", 0.01, False )
                have_ad = False

            if ( loc == None ):
                loc = openCV.sub_match_template( r"template\start\main.png", 0.01, False )
                if ( loc != None ):
                    in_main_page = True
            if ( loc == None ): # 是否在"內容實況版"
                loc = openCV.sub_match_template( r"template\quest\board.png", 0.01, False )
                if ( loc != None ): # 點擊"home"
                    loc = openCV.sub_match_template( r"template\quest\home.png", 0.01, False )
            if ( loc == None ): # 能量增幅組合包 點擊"關閉"
                loc = openCV.sub_match_template( r"template\start\energy_ad.png", 0.01, False )
                if ( loc != None ):
                    loc = [550,660]
                    have_ad = True
            if ( loc == None ): # 點擊"廣告關閉"
                loc = openCV.sub_match_template( r"template\start\main_ad_close.png", 0.01, False )
                if ( loc != None ):
                    have_ad = True
            if ( loc == None ): # 巨大頭目邀請 點擊"拒絕"
                loc = openCV.sub_match_template( r"template\start\invite.png", 0.01, False )
                if ( loc != None ):
                    loc = openCV.sub_match_template( r"template\start\reject.png", 0.01, False )
            if ( loc == None ): # 點擊"模擬器廣告關閉"
                loc = openCV.sub_match_template( r"template\start\emulator_ad_close.png", 0.01, False )
            if ( loc == None ): # 點擊"未來之戰"
                loc = openCV.sub_match_template( r"template\start\open_marvel.png", 0.01, False )
                if ( loc != None ):
                    wait_app_loading = True

            if ( loc == None ): # 非預期畫面出現
                error_occur = True
                error_num = 1

            if ( not in_main_page and loc != None ):
                adb.click( loc )
                if ( wait_app_loading ):
                    time.sleep(30)
                    wait_app_loading = False

        if ( in_main_page and not in_epic_quest ):  # 點擊"戰鬥入場"  error:2
            loc = openCV.sub_match_template( r"template\quest\enter.png", 0.01, False )
            if ( loc == None ): # 點擊"史詩任務"
                loc = openCV.sub_match_template( r"template\quest\epic_quest.png", 0.01, False )
            if ( loc == None ): # 是否在 "史詩任務" 裡
                loc = openCV.sub_match_template( r"template\quest\0\fate_of_mankind.png", 0.01, False )
                if ( loc != None ):
                    loc = None
                    in_epic_quest = True
                    find_epic = False
                    while( not find_epic ):
                        if ( topic == 0 ): # 點擊"人類命運"
                            loc = openCV.sub_match_template( r"template\quest\0\fate_of_mankind.png", 0.01, False )
                        elif ( topic == 1 ): # 點擊"黑暗統治"
                            loc = openCV.sub_match_template( r"template\quest\1\dark_reign.png", 0.01, False )
                        elif ( topic == 2 ): # 點擊"銀河號令"
                            loc = openCV.sub_match_template( r"template\quest\2\the_galactic_imperative.png", 0.01, False )
                        elif ( topic == 3 ): # 點擊"第一家庭"
                            loc = openCV.sub_match_template( r"template\quest\3\first_family.png", 0.01, False )
                        elif ( topic == 4 ): # 點擊"X特攻隊"
                            loc = openCV.sub_match_template( r"template\quest\4\x_force.png", 0.01, False )
                        elif ( topic == 5 ): # 點擊"X戰警崛起"
                            loc = openCV.sub_match_template( r"template\quest\5\rise_of_the_x_man.png", 0.01, False )

                        if ( loc == None ):
                            from_loc = [1000,400]
                            to_loc = [350,400]
                            adb.swipe( from_loc, to_loc, 300 )
                        else:
                            find_epic = True

            if ( loc == None ): # 非預期畫面出現
                error_occur = True
                error_num = 2

            if ( loc != None ):
                adb.click( loc )

        if ( in_epic_quest and not in_msn_prep ): #                  error:3
            loc = None
            if ( topic == 0 and not have_ad ):
                if ( loc == None and num % 3 == 0 ): # 點擊"真正的進化"
                    loc = openCV.sub_match_template( r"template\quest\0\true_evolution.png", 0.01, False )
                if ( loc == None and num % 3 != 0 ): # 點擊"英雄集結"
                    loc = openCV.sub_match_template( r"template\quest\0\heros_reunited.png", 0.01, False )
                    if ( loc == None and num % 3 == 1 ): # 點擊"瘋狂延燒"
                        loc = openCV.sub_match_template( r"template\quest\0\madness_ensues.png", 0.01, False )
                    if ( loc == None and num % 3 == 2 ): # 點擊"震驚和敬畏"
                        loc = openCV.sub_match_template( r"template\quest\0\shock_and_awe.png", 0.01, False )
            elif ( topic == 1 and not have_ad ):
                if ( loc == None and num % 3 == 0 ): # 點擊"扮演英雄"
                    loc = openCV.sub_match_template( r"template\quest\1\playing_hero.png", 0.01, False )
                if ( loc == None and num % 3 != 0 ): # 點擊"黃金神祇"
                    loc = openCV.sub_match_template( r"template\quest\1\golden_gods.png", 0.01, False )
                    if ( loc == None and num % 3 == 1 ): # 點擊"戰爭之神"
                        loc = openCV.sub_match_template( r"template\quest\1\god_of_war.png", 0.01, False )
                    if ( loc == None and num % 3 == 2 ): # 點擊"扭曲現實"
                        loc = openCV.sub_match_template( r"template\quest\1\twisted_reality.png", 0.01, False )
            elif ( topic == 2 and not have_ad ):
                if ( loc == None and num % 3 == 0 ): # 點擊"宇宙的命運"
                    loc = openCV.sub_match_template( r"template\quest\2\fate_of_the_universe.png", 0.01, False )
                if ( loc == None and num % 3 != 0 ): # 點擊"時空分裂"
                    loc = openCV.sub_match_template( r"template\quest\2\the_fault.png", 0.01, False )
                    if ( loc == None and num % 3 == 1 ): # 點擊"墮落使者"
                        loc = openCV.sub_match_template( r"template\quest\2\the_fallen_herald.png", 0.01, False )
                    if ( loc == None and num % 3 == 2 ): # 點擊"終極墮落"
                        loc = openCV.sub_match_template( r"template\quest\2\ultimate_corruption.png", 0.01, False )
            elif ( topic == 3 and not have_ad ):
                if ( loc == None and num % 3 == 0 ): # 點擊"破滅之日"
                    loc = openCV.sub_match_template( r"template\quest\3\dooms_day.png", 0.01, False )
                if ( loc == None and num % 3 != 0 ): # 點擊"扭曲的世界"
                    loc = openCV.sub_match_template( r"template\quest\3\twisted_world.png", 0.01, False )
                    if ( loc == None and num % 3 == 1 ): # 點擊"拉托維尼亞的冠軍"
                        loc = openCV.sub_match_template( r"template\quest\3\latverian_champion.png", 0.01, False )
                    if ( loc == None and num % 3 == 2 ): # 點擊"破滅的影子之下"
                        loc = openCV.sub_match_template( r"template\quest\3\in_the_shadow_of_doom.png", 0.01, False )
            elif ( topic == 4 and not have_ad ):
                if ( num < 15 ):
                    if ( loc == None and num % 3 == 0 ): # 點擊"混沌的起源"
                        loc = openCV.sub_match_template( r"template\quest\4\beginning_of_the_chaos.png", 0.01, False )
                    if ( loc == None and num % 3 != 0 ): # 點擊"笨蛋X戰警"
                        loc = openCV.sub_match_template( r"template\quest\4\stupid_x_man.png", 0.01, False )
                        if ( loc == None and num % 3 == 1 ): # 點擊"鍍鉻同伴"
                            loc = openCV.sub_match_template( r"template\quest\4\chrome_plated_comrade.png", 0.01, False )
                        if ( loc == None and num % 3 == 2 ): # 點擊"靈蝶拒之門外"
                            loc = openCV.sub_match_template( r"template\quest\4\psy_locked_out.png", 0.01, False )
                else: # 點擊"孿生小孩"
                    if ( loc == None ):
                        loc = openCV.sub_match_template( r"template\quest\4\the_big_twin.png", 0.01, False )
                    if ( loc == None and num % 3 == 1 ): # 點擊"切斷機堡"
                        loc = openCV.sub_match_template( r"template\quest\4\cutting_cable.png", 0.01, False )
                    if ( loc == None and num % 3 == 2 ): # 點擊"終結紛爭"
                        loc = openCV.sub_match_template( r"template\quest\4\ending_the_stryfe.png", 0.01, False )
            elif ( topic == 5 and not have_ad ):
                if ( loc == None and num % 3 == 0 ): # 點擊"共同的敵人"
                    loc = openCV.sub_match_template( r"template\quest\5\mutual_enemy.png", 0.01, False )
                if ( loc == None and num % 3 != 0 ): # 點擊"隱藏的秘密"
                    loc = openCV.sub_match_template( r"template\quest\5\veiled_secret.png", 0.01, False )
                    if ( loc == None and num % 3 == 1 ): # 點擊"萬磁王之力"
                        loc = openCV.sub_match_template( r"template\quest\5\magnetos_might.png", 0.01, False )
                    if ( loc == None and num % 3 == 2 ): # 點擊"鳳凰覺醒"
                        loc = openCV.sub_match_template( r"template\quest\5\rise_of_the_phoenix.png", 0.01, False )

            if ( have_ad ): # 關閉能量增幅組合包 點擊"確定"
                loc = openCV.sub_match_template( r"template\quest\ad_confirm.png", 0.01, False )
                have_ad = False
            if ( loc == None ): # 是否在 "任務準備" 裡
                loc = openCV.sub_match_template( r"template\quest\clear.png", 0.01, False )
                if ( loc != None ):
                    in_msn_prep = True
            if ( loc == None ): # 關閉能量增幅組合包 點擊"關閉"
                loc = openCV.sub_match_template( r"template\quest\ad_close.png", 0.01, False )
                if ( loc != None ):
                    have_ad = True
            if ( loc == None ): # 巨大頭目邀請 點擊"拒絕"
                loc = openCV.sub_match_template( r"template\start\invite.png", 0.01, False )
                if ( loc != None ):
                    loc = openCV.sub_match_template( r"template\start\reject.png", 0.01, False )
            if ( loc == None ): # 非預期畫面出現
                error_occur = True
                error_num = 3

            if ( not in_msn_prep and loc != None ):
                adb.click( loc )

        if ( in_epic_quest and in_msn_prep ): #                      error:4(team)、5
            if ( not check_team ): # 點擊 "隊伍"
                if ( team == 1 ):
                    loc = [685,120]
                elif ( team == 2 ):
                    loc = [785,120]
                elif ( team == 3 ):
                    loc = [880,120]
                elif ( team == 4 ):
                    loc = [980,120]
                elif ( team == 5 ):
                    loc = [1075,120]

                adb.click( loc )
                loc = None
                time.sleep(1)
                if ( team == 1 ):
                    loc = openCV.sub_match_template( r"template\team\one.png", 0.01, False )
                elif ( team == 2 ):
                    loc = openCV.sub_match_template( r"template\team\two.png", 0.01, False )
                elif ( team == 3 ):
                    loc = openCV.sub_match_template( r"template\team\three.png", 0.01, False )
                elif ( team == 4 ):
                    loc = openCV.sub_match_template( r"template\team\four.png", 0.01, False )
                elif ( team == 5 ):
                    loc = openCV.sub_match_template( r"template\team\five.png", 0.01, False )

                if ( loc != None ):
                    check_team = True
                else: # 非預期畫面出現
                    error_occur = True
                    error_num = 4

            if ( check_team ):
                if ( have_ad ): # 關閉能量增幅組合包 點擊"確定" 或是 點擊"廣告關閉確定"
                    loc = openCV.sub_match_template( r"template\quest\ad_confirm.png", 0.01, False )
                    have_ad = False
                elif ( quick_pass ): # 使用掃蕩卷
                    if ( not clear_quest ): # 點擊 "過關"
                        loc = openCV.sub_match_template( r"template\quest\clear.png", 0.01, False )
                        if ( loc == None ): # 點擊 "最多可使用X次"
                            loc = openCV.sub_match_template( r"template\quest\use_up_to.png", 0.01, False )
                        if ( loc == None ): # 檢查是否"過關"
                            loc = openCV.sub_match_template( r"template\quest\coin.png", 0.01, False )
                            if ( loc != None ):
                                clear_quest = True
                                totally_finished = True
                    else: # 點擊 "關閉"
                        loc = openCV.sub_match_template( r"template\quest\quest_use_ticket_close.png", 0.01, False )
                        if ( loc == None ): # 點擊 "home"
                            loc = openCV.sub_match_template( r"template\quest\home.png", 0.01, False )
                        if ( loc == None ): # 是否在"主頁面"
                            loc = openCV.sub_match_template( r"template\start\main.png", 0.01, False )
                            if ( loc != None ):
                                gAppCrash = False
                                break
                        if ( loc == None ): # 點擊"廣告關閉" ( 史塔克箱子MK2 )
                            loc = openCV.sub_match_template( r"template\start\main_ad_close.png", 0.01, False )
                            if ( loc != None ):
                                have_ad = True
                else:
                    if ( not clear_quest ): # 點擊 "自動重複"
                        loc = openCV.sub_match_template( r"template\quest\clear_ticket.png", 0.01, False )
                        if ( loc == None ): # 點擊 "MAX"
                            loc = openCV.sub_match_template( r"template\quest\max.png", 0.01, False )
                        if ( loc == None ): # 點擊 "開始"
                            loc = openCV.sub_match_template( r"template\quest\quest_start.png", 0.01, False )
                            if ( loc != None ):
                                clear_quest = True
                    else: # 點擊 "關閉"
                        loc = openCV.sub_match_template( r"template\quest\quest_close.png", 0.01, False )
                        if ( loc != None ):
                            totally_finished = True
                        if ( loc == None ): # 點擊 "home"
                            loc = openCV.sub_match_template( r"template\quest\quest_home.png", 0.01, False )
                        if ( loc == None ): # 是否在"主頁面"
                            loc = openCV.sub_match_template( r"template\start\main.png", 0.01, False )
                            if ( loc != None ):
                                gAppCrash = False
                                break
                        if ( loc == None ): # 點擊"廣告關閉" ( 史塔克箱子MK2 )
                            loc = openCV.sub_match_template( r"template\start\main_ad_close.png", 0.01, False )
                            if ( loc != None ):
                                have_ad = True
                        if ( loc == None and not totally_finished ): # 錯誤"素材滿了" 結束腳本
                            loc = openCV.sub_match_template( r"template\quest\material_full.png", 0.01, False )
                            if ( loc != None ):
                                gMatl_Full = True
                                break

                if ( loc != None ):
                    adb.click( loc )
                elif ( loc == None ): # 非預期畫面出現
                    error_occur = True
                    error_num = 5

                if ( clear_quest and not quick_pass and not wait_farm ):
                    for i in range(25):
                        time.sleep( 10 )
                        loc = openCV.sub_match_template( r"template\quest\quest_close.png", 0.01, False )
                        if ( loc != None ):
                            totally_finished = True
                            break

                    wait_farm = True

        if ( error_occur ):
            if ( loc == None ): # 點擊"模擬器廣告關閉"
                loc = openCV.sub_match_template( r"template\start\emulator_ad_close.png", 0.01, False )
                if ( loc != None ):
                    if ( not totally_finished ):
                        gAppCrash = True
            if ( loc == None ): # 點擊"未來之戰"
                loc = openCV.sub_match_template( r"template\start\open_marvel.png", 0.01, False )
                if ( loc != None ):
                    if ( not totally_finished ):
                        gAppCrash = True

            if ( gAppCrash ):
                break
            else:
                if ( error_num == 1 ):
                    adb.screenshot( "temp_screenshot\Error_1_unexcepted_pic_" + str(gError) + "_.png" )
                elif ( error_num == 2 ):
                    adb.screenshot( "temp_screenshot\Error_2_unexcepted_pic_" + str(gError) + "_.png" )
                elif ( error_num == 3 ):
                    adb.screenshot( "temp_screenshot\Error_3_unexcepted_pic_" + str(gError) + "_.png" )
                elif ( error_num == 4 ):
                    adb.screenshot( "temp_screenshot\Error_4_unexcepted_pic_" + str(gError) + "_.png" )
                elif ( error_num == 5 ):
                    adb.screenshot( "temp_screenshot\Error_5_unexcepted_pic_" + str(gError) + "_.png" )

                error_occur = False
                error_num = 0
                gError = int(gError) + 1

def Add_Energy(): # 增加能量
    global gError
    global gAppCrash
    in_main_page = False
    in_store = False
    in_alliance = False
    find_energy = False
    have_ad = False
    totally_finished = False
    wait_app_loading = False

    while ( True ):
        loc = None
        if ( not in_main_page ): # 是否在"主頁面"                     error:1
            if ( have_ad ): # 關閉能量增幅組合包 點擊"確定" 或是 點擊"廣告關閉確定"
                loc = openCV.sub_match_template( r"template\quest\ad_confirm.png", 0.01, False )
                have_ad = False

            if ( loc == None ):
                loc = openCV.sub_match_template( r"template\start\main.png", 0.01, False )
                if ( loc != None ):
                    in_main_page = True
            if ( loc == None ): # 是否在"內容實況版"
                loc = openCV.sub_match_template( r"template\quest\board.png", 0.01, False )
                if ( loc != None ): # 點擊"home"
                    loc = openCV.sub_match_template( r"template\quest\home.png", 0.01, False )
            if ( loc == None ): # 能量增幅組合包 點擊"關閉"
                loc = openCV.sub_match_template( r"template\start\energy_ad.png", 0.01, False )
                if ( loc != None ):
                    loc = [550,660]
                    have_ad = True
            if ( loc == None ): # 點擊"廣告關閉"
                loc = openCV.sub_match_template( r"template\start\main_ad_close.png", 0.01, False )
                if ( loc != None ):
                    have_ad = True
            if ( loc == None ): # 巨大頭目邀請 點擊"拒絕"
                loc = openCV.sub_match_template( r"template\start\invite.png", 0.01, False )
                if ( loc != None ):
                    loc = openCV.sub_match_template( r"template\start\reject.png", 0.01, False )
            if ( loc == None ): # 點擊"模擬器廣告關閉"
                loc = openCV.sub_match_template( r"template\start\emulator_ad_close.png", 0.01, False )
            if ( loc == None ): # 點擊"未來之戰"
                loc = openCV.sub_match_template( r"template\start\open_marvel.png", 0.01, False )
                if ( loc != None ):
                    wait_app_loading = True

        if ( in_main_page and not in_store ):
            loc = None
            if ( have_ad ):
                loc = openCV.sub_match_template( r"template\quest\ad_confirm.png", 0.01, False )
                have_ad = False

            if ( loc == None ): # 檢查是否在 "目錄" 裡
                loc = openCV.sub_match_template( r"template\alliance\contents.png", 0.01, False )
                if ( loc != None ): # 點擊 "聯盟"
                    loc = openCV.sub_match_template( r"template\alliance\alliance.png", 0.01, False )
            if ( loc == None ): # 點擊 "商店"
                loc = openCV.sub_match_template( r"template\alliance\store.png", 0.01, False )
                if ( loc != None ):
                    in_alliance = True
            if ( loc == None and not in_alliance ): # 點擊 "目錄"
                loc = openCV.sub_match_template( r"template\alliance\menu.png", 0.01, False )
            if ( loc == None ): # 點擊 "廣告關閉"
                loc = openCV.sub_match_template( r"template\start\main_ad_close.png", 0.01, False )
                if ( loc != None ):
                        have_ad = True
            if ( loc == None ): # 點擊 "廣告關閉"(高級制服升級卷組合包)
                loc = openCV.sub_match_template( r"template\quest\ad_close.png", 0.01, False )
                if ( loc != None ):
                        have_ad = True
            if ( loc == None ): # 是否在 "商店" 裡
                loc = openCV.sub_match_template( r"template\alliance\check_store.png", 0.01, False )
                if ( loc != None ):
                        in_store = True
            if ( loc == None ): # 檢查是否在 "完成挑戰課題" 裡
                loc = openCV.sub_match_template( r"template\start\achieve.png", 0.01, False )
                if ( loc != None ): # 完成挑戰課題 點擊"確定"
                    loc = openCV.sub_match_template( r"template\start\achieve_confirm.png", 0.01, False )

        if ( in_store and not find_energy ):
            loc = openCV.sub_match_template( r"template\alliance\energy.png", 0.01, False )
            if ( loc == None ): # 點擊 "能量"
                from_loc = [600,400]
                to_loc = [150,400]
                adb.swipe( from_loc, to_loc, 300 )
                loc = openCV.sub_match_template( r"template\alliance\energy.png", 0.01, False )

            if ( loc != None ):
                find_energy = True

        if ( in_store and find_energy ):
            if ( have_ad ): # 關閉能量增幅組合包 點擊"確定" 或是 點擊"廣告關閉確定"
                loc = openCV.sub_match_template( r"template\quest\ad_confirm.png", 0.01, False )
                have_ad = False

            if ( loc == None ): # 點擊 "購買"
                loc = openCV.sub_match_template( r"template\alliance\buy.png", 0.01, False )
            if ( loc == None ): # 點擊 "確定"
                loc = openCV.sub_match_template( r"template\alliance\buy_confirm.png", 0.01, False )
                if ( loc != None ):
                    totally_finished = True
            if ( loc == None ): # 點擊 "home"
                loc = openCV.sub_match_template( r"template\quest\home.png", 0.01, False )
            if ( loc == None ): # 檢查是否回主頁面
                loc = openCV.sub_match_template( r"template\start\main.png", 0.01, False )
                if ( loc != None ):
                    gAppCrash = False
                    break
            if ( loc == None ): # 點擊"廣告關閉"
                loc = openCV.sub_match_template( r"template\start\main_ad_close.png", 0.01, False )
                if ( loc != None ):
                    have_ad = True

        if ( loc != None ):
            adb.click( loc )
            if ( wait_app_loading ):
                time.sleep(30)
                wait_app_loading = False
        elif ( loc == None ):
            if ( loc == None ): # 點擊"模擬器廣告關閉"
                loc = openCV.sub_match_template( r"template\start\emulator_ad_close.png", 0.01, False )
                if ( loc != None ):
                    if ( not totally_finished ):
                        gAppCrash = True
            if ( loc == None ): # 點擊"未來之戰"
                loc = openCV.sub_match_template( r"template\start\open_marvel.png", 0.01, False )
                if ( loc != None ):
                    if ( not totally_finished ):
                        gAppCrash = True

            if ( gAppCrash ):
                break

            if ( loc == None ):
                adb.screenshot( "temp_screenshot\Error_Add_Energy()_unexcepted_pic_" + str(gError) + "_.png" )
                gError = int(gError) + 1

def Donation(): # 聯盟捐獻
    in_alliance = False
    have_ad = False
    finish_donate = False
    while ( True ):
        loc = None
        if ( have_ad ): # 關閉能量增幅組合包 點擊"確定" 或是 點擊"廣告關閉確定"
            loc = openCV.sub_match_template( r"template\quest\ad_confirm.png", 0.01, False )
            have_ad = False
        elif ( not in_alliance ):
            if ( loc == None ): # 檢查是否在 "目錄" 裡
                loc = openCV.sub_match_template( r"template\alliance\contents.png", 0.01, False )
                if ( loc != None ): # 點擊 "聯盟"
                    loc = openCV.sub_match_template( r"template\alliance\alliance.png", 0.01, False )
            if ( loc == None ): # 點擊 "捐獻"
                loc = openCV.sub_match_template( r"template\alliance\donate_one.png", 0.01, False )
                if ( loc != None ):
                    in_alliance = True
            if ( loc == None and not in_alliance ): # 點擊 "目錄"
                loc = openCV.sub_match_template( r"template\alliance\menu.png", 0.01, False )
            if ( loc == None ): # 點擊 "廣告關閉"
                loc = openCV.sub_match_template( r"template\start\main_ad_close.png", 0.01, False )
                if ( loc != None ):
                    have_ad = True
            if ( loc == None ): # 檢查是否在 "完成挑戰課題" 裡
                loc = openCV.sub_match_template( r"template\start\achieve.png", 0.01, False )
                if ( loc != None ): # 完成挑戰課題 點擊"確定"
                    loc = openCV.sub_match_template( r"template\start\achieve_confirm.png", 0.01, False )
        else:
            if ( loc == None and not finish_donate ): # 檢查是否在 "捐獻" 裡
                loc = openCV.sub_match_template( r"template\alliance\memento.png", 0.01, False )
                if ( loc != None ):
                    loc = openCV.sub_match_template( r"template\alliance\plus.png", 0.01, False )
                    for i in range(10):
                        adb.click( loc )
                    finish_donate = True

            loc = openCV.sub_match_template( r"template\alliance\donate_two.png", 0.01, False )
            if ( loc == None ):
                loc = openCV.sub_match_template( r"template\quest\ad_confirm.png", 0.01, False )
            if ( loc == None ):
                loc = openCV.sub_match_template( r"template\start\settings.png", 0.01, False )
            if ( loc == None ): # 點擊 "home"
                loc = openCV.sub_match_template( r"template\quest\home.png", 0.01, False )
            if ( loc == None ): # 檢查是否回主頁面
                loc = openCV.sub_match_template( r"template\start\main.png", 0.01, False )
                if ( loc != None ):
                    break
            if ( loc == None ): # 點擊 "廣告關閉"
                loc = openCV.sub_match_template( r"template\start\main_ad_close.png", 0.01, False )
                if ( loc != None ):
                    have_ad = True

        if ( loc != None ):
            adb.click( loc )

def World_Event(): # 世界活動
    global gAppCrash
    global gError
    start_battle = False
    in_main_page = False
    in_event_page = False
    in_prep_page = False
    have_ad = False
    error_occur = False
    error_num = 0
    error_count = 0  # 非預期畫面出現超過10次 結束程式
    totally_finished = False
    wait_app_loading = False

    while ( True ):
        loc = None
        if ( not in_main_page ): # 是否在"主頁面"                     error:1
            if ( have_ad ): # 關閉能量增幅組合包 點擊"確定" 或是 點擊"廣告關閉確定"
                loc = openCV.sub_match_template( r"template\quest\ad_confirm.png", 0.01, False )
                have_ad = False

            if ( loc == None ): # 是否在"主頁面"
                loc = openCV.sub_match_template( r"template\start\main.png", 0.01, False )
                if ( loc != None ):
                    in_main_page = True
            if ( loc == None ): # 是否在"內容實況版"
                loc = openCV.sub_match_template( r"template\quest\board.png", 0.01, False )
                if ( loc != None ): # 點擊"home"
                    loc = openCV.sub_match_template( r"template\quest\home.png", 0.01, False )
            if ( loc == None ): # 能量增幅組合包 點擊"關閉"
                loc = openCV.sub_match_template( r"template\start\energy_ad.png", 0.01, False )
                if ( loc != None ):
                    loc = [550,660]
                    have_ad = True
            if ( loc == None ): # 點擊"廣告關閉"
                loc = openCV.sub_match_template( r"template\start\main_ad_close.png", 0.01, False )
                if ( loc != None ):
                    have_ad = True
            if ( loc == None ): # 巨大頭目邀請 點擊"拒絕"
                loc = openCV.sub_match_template( r"template\start\invite.png", 0.01, False )
                if ( loc != None ):
                    loc = openCV.sub_match_template( r"template\start\reject.png", 0.01, False )
            if ( loc == None ): # 點擊"模擬器廣告關閉"
                loc = openCV.sub_match_template( r"template\start\emulator_ad_close.png", 0.01, False )
            if ( loc == None ): # 點擊"未來之戰"
                loc = openCV.sub_match_template( r"template\start\open_marvel.png", 0.01, False )
                if ( loc != None ):
                    wait_app_loading = True
            if ( loc == None ): # 非預期畫面出現
                error_occur = True
                error_num = 1
                error_count += 1

        if ( in_main_page and not in_event_page ): # 點擊 "世界活動"
            loc = None                # 點擊 "世界活動 第二格"
            loc = openCV.sub_match_template( r"template\event\worldevent_2.png", 0.01, False )
            if ( loc == None ):       # 點擊 "世界活動 第三格"
                loc = openCV.sub_match_template( r"template\event\worldevent_3.png", 0.01, False )
            if ( loc == None ):       # 點擊 "世界活動 第四格"
                loc = openCV.sub_match_template( r"template\event\worldevent_4.png", 0.01, False )
            if ( loc == None ):       # 是否在 "戰鬥準備" 頁面
                loc = openCV.sub_match_template( r"template\event\worldevent.png", 0.01, False )
                if ( loc != None ):
                    in_event_page = True
            if ( loc == None ):       # 非預期畫面出現
                error_occur = True
                error_num = 2
                error_count += 1

        if ( in_event_page and not in_prep_page ):
            loc = None          # 點擊 "戰鬥準備"
            loc = openCV.sub_match_template( r"template\event\battleprepare.png", 0.01, False )
            if ( loc == None ): # 點擊 "準備就緒-1"
                loc = openCV.sub_match_template( r"template\event\ready_one.png", 0.01, False )
            if ( loc == None ): # 點擊 "準備就緒-2"
                loc = openCV.sub_match_template( r"template\event\ready_two.png", 0.01, False )
            if ( loc == None ): # 點擊 "確定"
                loc = openCV.sub_match_template( r"template\event\confirm.png", 0.01, False )
            if ( loc == None ): # 點擊 "開始"
                loc = openCV.sub_match_template( r"template\event\start.png", 0.01, False )
                if ( loc != None ):
                    start_battle  = True
                    in_prep_page  = True
            if ( loc == None ): # 非預期畫面出現
                error_count += 1
                if ( error_count > 2 ):
                    error_occur = True
                    error_num = 3

        if( ( in_event_page and in_prep_page ) ):
            if ( have_ad ): # 關閉能量增幅組合包 點擊"確定" 或是 點擊"廣告關閉確定"
                loc = openCV.sub_match_template( r"template\quest\ad_confirm.png", 0.01, False )
                have_ad = False
            
            if ( loc == None ): # 點擊 "home"
                loc = openCV.sub_match_template( r"template\event\home.png", 0.01, False )
                if ( loc != None ):
                    totally_finished = True
                    gAppCrash = False
            if ( loc == None ): # 檢查是否在主頁面
                loc = openCV.sub_match_template( r"template\start\main.png", 0.01, False )
                if ( loc != None ):
                    break
            if ( loc == None ): # 點擊"廣告關閉"
                loc = openCV.sub_match_template( r"template\start\main_ad_close.png", 0.01, False )
                if ( loc != None ):
                    have_ad = True
            if ( loc == None ): # 非預期畫面出現
                error_occur = True
                error_num = 4
                error_count += 1

        if ( loc != None ):
            adb.click( loc )
            if ( wait_app_loading ):
                time.sleep(30)
                wait_app_loading = False
        elif ( error_occur ):
            if ( loc == None ): # 點擊"模擬器廣告關閉"
                loc = openCV.sub_match_template( r"template\start\emulator_ad_close.png", 0.01, False )
                if ( loc != None ):
                    if ( not totally_finished ):
                        gAppCrash = True
            if ( loc == None ): # 點擊"未來之戰"
                loc = openCV.sub_match_template( r"template\start\open_marvel.png", 0.01, False )
                if ( loc != None ):
                    if ( not totally_finished ):
                        gAppCrash = True

            if ( gAppCrash ):
                break
            else:
                if ( error_num == 1 ):
                    adb.screenshot( "temp_screenshot\Error_World_Event_1_unexcepted_pic_" + str(gError) + "_.png" )
                elif ( error_num == 2 ):
                    adb.screenshot( "temp_screenshot\Error_World_Event_2_unexcepted_pic_" + str(gError) + "_.png" )
                elif ( error_num == 3 ):
                    adb.screenshot( "temp_screenshot\Error_World_Event_3_unexcepted_pic_" + str(gError) + "_.png" )
                elif ( error_num == 4 ):
                    adb.screenshot( "temp_screenshot\Error_World_Event_3_unexcepted_pic_" + str(gError) + "_.png" )

                error_occur = False
                error_num = 0
                gError = int(gError) + 1

            if ( error_count > 10 ):
                break

        if ( start_battle ):
            for i in range(20):
                loc = [400,400]
                time.sleep( 10 )
                adb.click( loc )
                if ( i > 17 ):
                    loc = None
                    loc = openCV.sub_match_template( r"template\event\home.png", 0.01, False )
                    if ( loc != None ):
                        break

            start_battle = False

def Reach_Target_Hour( num ):
    current_Date_And_Time = datetime.now()
    now_Hour = int(current_Date_And_Time.strftime("%H"))

    if ( num == now_Hour ):
        return True

    return False

def Reach_Target_Mins( num ):
    current_Date_And_Time = datetime.now()
    now_Mins = int(current_Date_And_Time.strftime("%M"))

    if ( num == now_Mins ):
        return True

    return False

def Set_World_Event():
    global gMins
    current_Date_And_Time = datetime.now()
    now_Mins = int(current_Date_And_Time.strftime("%M"))
    tempNum = int(gMins) - int(now_Mins)
    if ( tempNum > 6 ):
        return True
    else:
        return False

def Detect_App_Crash( num ):
    global gAppCrash
    global last_topic
    global last_team
    global last_num
    global last_quick_pass

    if ( gAppCrash and num == 0 ):  # Start_Quest
        while ( gAppCrash ):
            gAppCrash = False
            Start_Quest( last_topic, last_team, last_num, last_quick_pass )
    elif( gAppCrash and num == 1 ): # Add_Energy
        while ( gAppCrash ):
            gAppCrash = False
            Add_Energy()
    elif( gAppCrash and num == 2 ): # World_Event
        while ( gAppCrash ):
            gAppCrash = False
            World_Event()
#------------------ main ------------------
settings_path =  r"settings.txt"
int_vars = ["change_time","Change_progress", "target_hour", "target_mins", "first_world_event", "second_world_event", "server_maintain", "Use_current_time"]
string_vars = ["adb_path","device_address"]
gHour = 0
gMins = 0
gCount = 0
gError = 1
gEvent = 0  # 刷關結束後打世界活動(1)
gAppCrash = False
gMatl_Full = False
gEmulator_Error = False
gMaintain = 0

last_topic = 0
last_team = 0
last_num = 0
last_quick_pass = False
Read_file() # 讀檔
gMaintain = int(settings.server_maintain)
Set_Target_Time( settings.change_time )
loc = openCV.sub_match_template( r"template\start\main.png", 0.01, False )
print( "==============================================" + '\n' + "Start Scripts Start Scripts Start Scripts" + '\n' + "==============================================" + '\n' )
while ( True ):
    if ( Time_To_start() ):
        if ( gMaintain == 1 ):
            if ( Reach_Target_Hour(6) and Reach_Target_Mins(59) ):
                break
            if ( gHour == 7 ):
                break

        if ( gCount == 0 ):
            Start_Quest( 3, 2, 0, False ) # 破滅之日
            Detect_App_Crash( 0 )
            Start_Quest( 3, 2, 1, False ) # 扭曲的世界(拉托維尼亞的冠軍)
            Detect_App_Crash( 0 )
            Start_Quest( 3, 2, 2, False ) # 扭曲的世界(破滅的影子之下)
            Detect_App_Crash( 0 )
            Donation()
        elif ( gCount == 1 ):
            Start_Quest( 2, 2, 3, False ) # 宇宙的命運
            Detect_App_Crash( 0 )
            Start_Quest( 2, 2, 4, False ) # 時空分裂(墮落使者)
            Detect_App_Crash( 0 )
            Start_Quest( 2, 2, 5, False ) # 時空分裂(終極墮落)
            Detect_App_Crash( 0 )
        elif ( gCount == 2 ):
            Start_Quest( 1, 2, 6, False ) # 扮演英雄
            Detect_App_Crash( 0 )
            Start_Quest( 1, 2, 7, False ) # 黃金神祇(戰爭之神)
            Detect_App_Crash( 0 )
            Start_Quest( 1, 2, 8, False ) # 黃金神祇(扭曲現實)
            Detect_App_Crash( 0 )
        elif ( gCount == 3 ):
            Add_Energy()
            Detect_App_Crash( 1 )
            Start_Quest( 0, 2, 9, False ) # 真正的進化
            Detect_App_Crash( 0 )
            Start_Quest( 0, 2, 10, False ) # 英雄集結(瘋狂延燒)
            Detect_App_Crash( 0 )
            Start_Quest( 0, 2, 11, False ) # 英雄集結(震驚和敬畏)
            Detect_App_Crash( 0 )
        elif ( gCount == 4 ):
            Add_Energy()
            Detect_App_Crash( 1 )
            Start_Quest( 4, 2, 12, False ) # 混沌的起源
            if ( gMatl_Full ): break
            Detect_App_Crash( 0 )
            Start_Quest( 4, 2, 13, False ) # 笨蛋Ｘ戰警(鍍鉻同伴)
            Detect_App_Crash( 0 )
            Start_Quest( 4, 2, 14, False ) # 笨蛋Ｘ戰警(靈蝶拒之門外)
            Detect_App_Crash( 0 )
            Start_Quest( 5, 2, 15, False ) # 共同的敵人
            if ( gMatl_Full ): break
            Detect_App_Crash( 0 )
        elif ( gCount == 5 ):
            Add_Energy()
            Detect_App_Crash( 1 )
            Start_Quest( 5, 2, 16, True ) # 隱藏的秘密(萬磁王之力)
            Detect_App_Crash( 0 )
            Start_Quest( 5, 2, 17, True ) # 隱藏的秘密(鳳凰覺醒)
            Detect_App_Crash( 0 )
            Start_Quest( 4, 2, 19, True ) # 孿生小孩(切斷機堡)
            Detect_App_Crash( 0 )
            Start_Quest( 4, 2, 20, True ) # 孿生小孩(終結紛爭)
            Detect_App_Crash( 0 )

        if ( gEvent == 1 ):
            World_Event()
            Detect_App_Crash( 3 )
            gEvent = 0

        if ( gCount == 0 or gCount == 1 ):
            Add_Target_Time( 1 )
        else:
            Add_Target_Time( 2 )

    if ( gMaintain == 1 and gHour == 7 ):
        print( "==============================================" + '\n' + "Time to maintain, finish scripts" + '\n' + "==============================================" + '\n' )
        break

    if ( gCount > 5 and settings.second_world_event == 1 ):
        break

    if ( gCount > 5 and settings.second_world_event == 0 ):
        if ( Reach_Target_Hour(7) ):
            World_Event()
            Detect_App_Crash( 3 )
            break
    elif ( Reach_Target_Hour(1) and settings.first_world_event == 0 ):
        if ( gHour == 1 ):
            if ( Set_World_Event() ):
                World_Event()
                Detect_App_Crash( 3 )
            else:
                gEvent = 1
        else:
            World_Event()
            Detect_App_Crash( 3 )

        settings.first_world_event = 1
    elif ( Reach_Target_Hour(7) and settings.second_world_event == 0 ):
        if ( gHour == 7 ):
            if ( Set_World_Event() ):
                World_Event()
                Detect_App_Crash( 3 )
            else:
                gEvent = 1
        else:
            World_Event()
            Detect_App_Crash( 3 )

        settings.second_world_event = 1

    time.sleep(15)
    #os.system("pause")
print( "==============================================" + '\n' + "Finish Scripts Finish Scripts Finish Scripts" + '\n' + "==============================================" + '\n' )

"""
from_loc = [1000,400]
to_loc = [150,400]
use_time = 300
adb.swipe( from_loc, to_loc, use_time )
"""
"""
loca = openCV.abc( r"template\start\menu.png", 0.01, False )
if ( loca != None ):
    adb.click( loca )
"""
#script_file = os.path.realpath(__file__) 絕對路徑
#dirname = os.path.dirname(script_file)   獲取目錄
#settings_path = dirname + "\settings.txt"
#screenshot_path = dirname + r"\temp_screenshot"
#adb.screenshot( r"temp_screenshot\screenshot.png" )

#loc = openCV.match_template( r"1.png", r"template\start\main_ad_close.png", 0.01, False )
#loc = openCV.match_template( r"2.png", r"template\start\main_ad_close.png", 0.01, False )
#loc = openCV.match_template( r"3.png", r"template\start\main_ad_close.png", 0.01, False )
#loc = openCV.match_template( r"4.png", r"template\start\main_ad_close.png", 0.01, False )
#loc = openCV.match_template( r"5.png", r"template\start\main_ad_close.png", 0.01, False )

#loc = openCV.match_template( r"aaa.png", r"template\quest\quest_use_ticket_close.png", 0.01, False )
#loc = openCV.match_template( r"bbb.png", r"template\quest\quest_use_ticket_close.png", 0.01, False )
#loc = openCV.match_template( r"ccc.png", r"template\quest\quest_use_ticket_close.png", 0.01, False )
#loc = openCV.match_template( r"aaa.png", r"template\quest\quest_close.png", 0.01, False )
#loc = openCV.match_template( r"bbb.png", r"template\quest\quest_close.png", 0.01, False )
#loc = openCV.match_template( r"ccc.png", r"template\quest\quest_close.png", 0.01, False )
#loc = openCV.match_template( r"aaa.png", r"template\quest\ad_close.png", 0.01, False )
#loc = openCV.match_template( r"bbb.png", r"template\quest\ad_close.png", 0.01, False )
#loc = openCV.match_template( r"ccc.png", r"template\quest\ad_close.png", 0.01, False )
"""
count = 0
if ( num == 0 or num == 3 or num == 12 or num == 15 ): # time.sleep( 95 )
count = 10
elif ( num == 5 or num == 9 or num == 10 or num == 11 ): # time.sleep( 180 )
count = 18
else: # time.sleep( 240 )
count = 24
"""