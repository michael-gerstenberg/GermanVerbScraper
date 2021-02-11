from python_anticaptcha import AnticaptchaClient, ImageToTextTask
import config

def solve_captcha(img_path):
    captcha_fp = open(img_path, 'rb')
    client = AnticaptchaClient(config.captcha_api_key)
    task = ImageToTextTask(captcha_fp)
    job = client.createTask(task)
    job.join()
    return job.get_captcha_text()