import torch
import transformers

from backend.utils import params

MAX_LEN = params.token_max_len
pretrained_model = params.sentiment_model
tokenizer_model = params.tokenizer_model

config = transformers.AutoConfig.from_pretrained(
    pretrained_model, num_labels=3, local_files_only=True
)
xlm_model = transformers.AutoModelForSequenceClassification.from_pretrained(
    pretrained_model, config=config
)
tokenizer = transformers.AutoTokenizer.from_pretrained(params.tokenizer_model)


def predict(text: str) -> int:
    text = text.split("|@|")
    clean_text = [i for i in text if len(i) >= 15]
    sentiments = []

    for piece in clean_text:
        tokenized = tokenizer(
            piece, truncation=True, padding="max_length", max_length=MAX_LEN
        )
        outputs = xlm_model(
            input_ids=torch.Tensor(tokenized["input_ids"]).unsqueeze(0).to(torch.int64),
            attention_mask=torch.Tensor(tokenized["attention_mask"])
            .unsqueeze(0)
            .to(torch.int64),
        )
        _, preds = torch.max(outputs[0], dim=1)
        prediction = int(preds[0])
        sentiments.append(prediction)

    counts = {str(i): sentiments.count(i) for i in range(0, 3)}
    counts = dict(sorted(counts.items(), key=lambda item: item[1]))

    most = counts[list(counts.keys())[-1]]
    most_label = list(counts.keys())[-1]
    # TODO label choice if equal

    return int(most_label)


def predict_one(text: str) -> int:
    tokenized = tokenizer(
        text, truncation=True, padding="max_length", max_length=MAX_LEN
    )
    outputs = xlm_model(
        input_ids=torch.Tensor(tokenized["input_ids"]).unsqueeze(0).to(torch.int64),
        attention_mask=torch.Tensor(tokenized["attention_mask"])
        .unsqueeze(0)
        .to(torch.int64),
    )
    _, preds = torch.max(outputs[0], dim=1)
    prediction = int(preds[0])
    return prediction
