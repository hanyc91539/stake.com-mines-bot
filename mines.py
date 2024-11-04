from datetime import datetime
from time import sleep
from threading import Thread
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
import keyboard
import random
import requests
import json


RESULT_WINN = "Win"
RESULT_LOSS = "Loss"

initChipValue = 0.0001

betOption = {}
with open("strategy.json", "r") as file:
    betOption = json.load(file)


BUTTON_BET = 'Bet'
BUTTON_HALF = '1/2'
BUTTON_DOUBLE = '2x'

ID = {
    BUTTON_BET: "bet-button",
    BUTTON_HALF: "input-button-wrap@0",
    BUTTON_DOUBLE: "input-button-wrap@1",
}

pressedKey = False

Is_End = False

url = "https://stake.com/casino/games/mines"

options = Options()
options.add_experimental_option("debuggerAddress", "127.0.0.1:9030") #9030
options.add_argument("user-agent=Chrome/121.0.6167.185")
driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)

def clickButton(buttonName):
    if not pressedKey:
        button = None
        buttonId = ID[buttonName]
        if "input-button-wrap" in buttonId:
            button = findElement(driver, By.CLASS_NAME, "input-button-wrap").find_elements(
                By.TAG_NAME, 'button')[int(buttonId.split("@")[1])]
        else:
            button = findElement(driver, By.CSS_SELECTOR,
                                 f'button[data-testid="{ID[buttonName]}"]')
        if button != None:
            try:
                button.click()
            except:
                driver.execute_script("arguments[0].click();", button)
            print(
                f'{datetime.now().strftime("%H:%M:%S")}, button clicked <{buttonName}>')
            sleep(0.5)


def clickSquares(numbers):
    findElement(driver, By.CSS_SELECTOR, 'button[data-testid="cashout-button"]')
    while not pressedKey:
        try:
            squareButtons = findElement(driver, By.CLASS_NAME, 'game-content').find_elements(By.TAG_NAME, 'button')
            for number in numbers:
                sleep(0.1)
                try:
                    driver.find_element(By.CSS_SELECTOR, f'button[data-testid="{ID[BUTTON_BET]}"]')
                    return RESULT_LOSS
                except:
                    pass
                try:
                    if squareButtons[number - 1].get_attribute("data-revealed") == "false":
                        squareButtons[number - 1].click()
                except:
                    pass
            if squareButtons[numbers[-1] - 1].get_attribute("data-revealed") == "true":
                break
            sleep(0.2)
        except:
            pass
        sleep(0.1)


def check_if_win_or_not():
    result = RESULT_LOSS
    while True:
        try:
            cashoutButton = driver.find_element(By.CSS_SELECTOR, 'button[data-testid="cashout-button"]')
            if cashoutButton.text == "Cashout":
                result = RESULT_WINN
                while True:
                    cashoutButton.click()
                    try:
                        driver.find_element(By.CSS_SELECTOR, f'button[data-testid="bet-button"]')
                        break
                    except:
                        pass
                    sleep(0.1)
                break
        except:
            pass
        try:
            driver.find_element(By.CSS_SELECTOR, f'button[data-testid="bet-button"]')
            break
        except:
            pass
        sleep(0.1)
    return result


def setMines(minesCount):
    if minesCount > 0 and minesCount < 25:
        selectElement = findElement(driver, By.NAME, 'mines-count')
        if selectElement != None:
            select = Select(selectElement)
            select.select_by_value(str(minesCount))
            print(f'{datetime.now().strftime("%H:%M:%S")}, Mines: {minesCount}')
            sleep(0.5)
    else:
        print(
            f'{datetime.now().strftime("%H:%M:%S")}, Mines should be in [1, 24]')


def findElement(driver, by, value):
    element = None
    timeout = 0
    refreshed = False
    while not pressedKey:
        try:
            element = driver.find_element(by, value)
            break
        except:
            if value == 'button[data-testid="cashout-button"]':
                timeout += 0.1
        if not refreshed and timeout >= 5.0:
            driver.refresh()
            refreshed = True
        sleep(0.1)
    return element


def getTotalAmount():
    totalAmountElement = findElement(driver, By.CLASS_NAME, 'coin-toggle')
    totalAmount = -1
    if totalAmountElement != None:
        totalAmount = float(totalAmountElement.text)
    return totalAmount


def setChipValue(chipValue):
    chipValueInput = findElement(driver, By.CLASS_NAME, 'input-content').find_element(By.TAG_NAME, 'input')
    if chipValueInput != None:
        chipValueInput.send_keys(str(chipValue))
        print(f'{datetime.now().strftime("%H:%M:%S")}, Bet Amount: {chipValue}')
        sleep(0.5)


def rearrangeSquares():
    unique_numbers = set()
    while len(unique_numbers) < betOption["Selected Mines"]:
        unique_numbers.add(random.randint(1, 25))
    squares = list(unique_numbers)
    print(f'{datetime.now().strftime("%H:%M:%S")}, Rearranged Squares: {squares}')
    return squares


def pressKey():
    global pressedKey
    while not Is_End:
        if keyboard.is_pressed('esc'):
            pressedKey = True
            print(f'{datetime.now().strftime("%H:%M:%S")} Pressed the [ESC] key\n')
        sleep(0.1)


def Martingale():
    global Is_End
    global pressedKey
    
    chipValue = initChipValue
    countWinn = 0
    countLoss = 0

    squares = rearrangeSquares()
    
    while not Is_End:
        setMines(betOption["Total Mines"])

        setChipValue(chipValue)

        clickButton(BUTTON_BET)

        clickSquares(squares)

        result = check_if_win_or_not()

        if result == RESULT_WINN:
            countWinn += 1
        else:
            countLoss += 1
            countWinn = 0
        
        output = f'{datetime.now().strftime("%H:%M:%S")}, {result} ({countWinn} : {countLoss})'
        print(output)
        # with open('statistics.txt', '+a') as file:
        #     file.write(output + "\n")

        if countWinn == betOption["Win"]["Count"]:
            chipValue = initChipValue
            countWinn = 0
            # countLoss = 0
        if countLoss == betOption["Loss"]["Count"]:
            chipValue *= betOption[result]["Multiplier"]
            countLoss = 0
        
        totalAmount = getTotalAmount()
        if chipValue > totalAmount and totalAmount != -1:
            print("There is not enough money to bet.")
            break
        else:
            if betOption[result]["Rearrange"]:
                squares = rearrangeSquares()
        print("\n")

        if pressedKey:
            print("\n")
            response = input(
                "It has now stopped running. Press the [y] key to run again, the [n] key to exit.")
            if response == "y":
                print("\n")
                input(
                    "To run it again, you need to reset all states. Press the [Enter] key after initializing.")
                print("\n")
                pressedKey = False
            else:
                break
    print(f'{datetime.now().strftime("%H:%M:%S")}, Ended')
    Is_End = True


def userVerify(url, payload):    
    global pressedKey
    global Is_End
    
    while True:
        sleep(3600)
        response = requests.request("POST", url, data=payload)
        data = response.json()["data"]
        print("")
        print(data + "\n")
        if data != "Successfully verified":
            pressedKey = True
            Is_End = True
            break


if __name__ == "__main__":
    while True:
        username = input("username: ")
        print("")
        password = input("password: ")
        print("")
        
        url = "http://87.251.88.14:80/login"

        payload = {
            'username': username,
            'password': password,
            'client_id': '123',
            'productName' : "mines"
            }

        response = requests.request("POST", url, data=payload)
        data = response.json()["data"]
        
        print(data)
        print("")
        
        if data == "Successfully verified":
            break
        
    Thread(target=pressKey).start()
    Thread(target=userVerify, args=(url, payload, )).start()
    Martingale()
