class Preprocessor:
    def __init__(self, tokenizer, max_length=64):
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __call__(self, examples):
        return self.tokenizer(
            examples['text'], 
            truncation=True, 
            padding='max_length', 
            max_length=self.max_length
        )