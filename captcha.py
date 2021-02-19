from python_anticaptcha import AnticaptchaClient, ImageToTextTask
import config
import requests
import shutil
import mechanicalsoup

def solve_captcha(img_path):
    captcha_fp = open(img_path, 'rb')
    client = AnticaptchaClient(config.captcha_api_key)
    task = ImageToTextTask(captcha_fp)
    job = client.createTask(task)
    job.join()
    return job.get_captcha_text()

def solve_captcha_netzverb(url, image_url):
    filename = 'captcha.png'
    r = requests.get(image_url, stream = True)
    if r.status_code == 200:
        r.raw.decode_content = True
        with open(filename,'wb') as f:
            shutil.copyfileobj(r.raw, f)
        print('Captcha is getting solved...')
        try:
            answer = solve_captcha('captcha.png')
        except:
            return False
        browser = mechanicalsoup.StatefulBrowser()
        browser.open(url)
        # browser.select_form().print_summary()
        browser.select_form()
        try:
            browser["captcha"] = answer
        except:
            return
        browser.submit_selected()
        return
    else:
        print('Image couldn\'t be retrieved. Trying again ...')
        return
