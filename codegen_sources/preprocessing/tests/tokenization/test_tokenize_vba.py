from codegen_sources.preprocessing.lang_processors.vba_processor import VbaProcessor

processor = VbaProcessor()


def test_vba_tokenizer():
    x = '/home/jerry/PycharmProjects/CodeGen/codegen_sources/input.txt'
    y, z = processor.get_vba_tokens_and_types(x)  # .tokenize_code(x)
    print(y)
    print(z)


if __name__ == '__main__':
    test_vba_tokenizer()
