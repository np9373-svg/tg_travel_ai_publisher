from models.schemas import GenerateRequest, GenerateResponse, GenerateData
import openai
from yandex_cloud_ml_sdk import YCloudML
from yandex_cloud_ml_sdk.auth import APIKeyAuth
from config.settings import settings
import base64

import logging
logger = logging.getLogger("generator")

client = openai.OpenAI(
    api_key=settings.OPENAI_KEY,
    base_url=settings.OPENAI_BASE_URL
)

sdk = YCloudML(
    folder_id= settings.FOLDER_ID,
    auth=APIKeyAuth(api_key=settings.YC_API_KEY),
)


def generate_text(payload: GenerateRequest, system_prompt_file_path: str):
    # Достаточно ли тезисов для генерации
    if len(payload.summary) < 3:
        logger.info("В саммари меньше трех тезисов. Недостаточно данных для подготовки информационного поста.")
        return "Недостаточно данных для подготовки информационного поста."

    # Подготовка пользовательского промпта
    user_prompt = "Саммари:\n"
    user_prompt += "\n".join(f"- {item}" for item in payload.summary)
    user_prompt += "\n\nКонец саммари."

    # Подготовка системного промпта
    with open(system_prompt_file_path, "r", encoding="utf-8") as f:
        system_prompt = f.read()

    # Обращение к модели
    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
            temperature=0.3,
        timeout=120.0
        )
    generated_text = response.choices[0].message.content

    if generated_text != "Недостаточно данных для подготовки информационного поста.":
        generated_text += f"\nИсточник: {payload.link}"
    else:
        logger.info("Модель вернула ответ: Недостаточно данных для подготовки информационного поста.")

    logger.info(f"Текст поста сгенерирован.")
    return generated_text
        
def generate_visual_image(payload: GenerateRequest, system_prompt_file_path: str):
    # Подготовка пользовательского промпта
    user_prompt = "Саммари:\n"
    user_prompt += "\n".join(f"- {item}" for item in payload.summary)
    user_prompt += "\n\nКонец саммари."

    # Подготовка системного промпта
    with open(system_prompt_file_path, "r", encoding="utf-8") as f:
        system_prompt = f.read()

    # Обращение к модели
    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
            temperature=0.3,
        timeout=120.0
        )
    generated_text = response.choices[0].message.content
    logger.info(f"Промпт для генерации фото:\n{generated_text}")
    return generated_text

def generate_image(visual_image_description: str, style_format_file_path:str):
    # Подготовка системного промпта
    with open(style_format_file_path, "r", encoding="utf-8") as f:
        style_format = f.read()

    prompt='[STYLE / RULES / FORMAT]\n' + style_format + '[OBJECT DESCRIPTION]\n' + visual_image_description

    model = (
        sdk.models.image_generation("yandex-art")
        .configure(
            width_ratio=1,
            height_ratio=1,  # 1024x1024
            seed=50,
        )
    )

    operation = model.run_deferred(prompt)
    result = operation.wait(timeout=600)

    if result is None:
        logger.error(f"Изображение сгенерировано некорректно: пустой ответ")
        return  None

    image_bytes = getattr(result, "image_bytes", None)

    if not image_bytes:
        logger.error(f"Изображение сгенерировано некорректно: нет image_bytes")
        return None

    # минимальная проверка, что это действительно изображение
    # JPEG начинается с FF D8, PNG с 89 50 4E 47
    if not (
            image_bytes.startswith(b"\xff\xd8") or
            image_bytes.startswith(b"\x89PNG")
    ):
        logger.error(f"Изображение сгенерировано некорректно: объект не является изображением")
        return None

    logger.info(f"Изображение сгенерировано успешно")
    return image_bytes



def generate_content(payload: GenerateRequest) -> GenerateResponse:
    try:
        # генерация текста поста
        generated_text = generate_text(payload, "services/text_generation_system_prompt.txt")

        # текст поста не сформирован моделью
        if generated_text == "Недостаточно данных для подготовки информационного поста.":
            return GenerateResponse(
                status='summary_too_short',
                data=None,
                error_message=None)

        #генерация описания объекта на фото
        generated_visual_image = generate_visual_image(payload, "services/visual_image_generation_system_prompt.txt")

        # генерация картинки
        try:
            image_bytes = generate_image(generated_visual_image, "services/style_prompt.txt")
        except TimeoutError as e:
            logger.error(str(e))
            return GenerateResponse(
                status="error",
                data=None,
                error_message="yandex_art_timeout_over"
            )

        # картинка не сформирована моделью
        if not image_bytes:
            return GenerateResponse(
                status='error',
                data=None,
                error_message='image_generation_failed')

        # кодирование картинки для отправки в json
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")

        # happy route завершен
        return GenerateResponse(
            status='success',
            data=GenerateData(
                text=generated_text,
                image_base64=image_base64
            ),
            error_message=None)


    except openai.APITimeoutError as e:
        logger.error(str(e))
        return GenerateResponse(
            status="error",
            data=None,
            error_message="openai_timeout_over"
        )
    except Exception as e:
        logger.error(str(e))
        return GenerateResponse(
            status="error",
            data=None,
            error_message="llm_not_available"
        )



