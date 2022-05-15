from codegen_sources.preprocessing.lang_processors.vba_processor import VbaProcessor

processor = VbaProcessor()

TESTS = []
TESTS.append(r"""
Sub List_All_The_Files_Within_Path()
    Dim Row_No As Integer
    Dim No_Of_Files As Integer
    Dim kk25 As Integer
    Dim File_Path As String

    File_Path = "C:My Documents"
    Row_No = 36

    'Lists all the files in the current directory
    With Application.FileSearch
        .NewSearch
        .LookIn = File_Path
        .Filename = "*.*"
        .SearchSubFolders = False
        .Execute

        No_Of_Files = .FoundFiles.Count

        For kk25 = 1 To No_Of_Files
            Worksheets("Sheet1").Cells(kk25 + 5, 15).Value = .FoundFiles(kk25)
        Next kk25
    End With
End Sub""")

# TESTS.append(r"""
# include <iostream>
# using namespace std;
#
# int main() {
#     float n1, n2, n3;
#
#     cout << "Enter three numbers: ";
#     cin >> n1 >> n2 >> n3;
#
#     if(n1 >= n2 && n1 >= n3)
#         cout << "Largest number: " << n1;
#
#     if(n2 >= n1 && n2 >= n3)
#         cout << "Largest number: " << n2;
#
#     if(n3 >= n1 && n3 >= n2)
#         cout << "Largest number: " << n3;
#
#     return 0;
# }""")

def test_get_vba_tokens_and_types():
    x = '/home/jerry/PycharmProjects/CodeGen/codegen_sources/input.txt'
    y, z = processor.get_vba_tokens_and_types(x)  # .tokenize_code(x)
    print(y)
    print(z)

def test_vba_tokenize_code():
    print("OK")
    for x in TESTS:
        y = processor.tokenize_code(x)
    return y


if __name__ == '__main__':
    # test_get_vba_tokens_and_types()
    txt = test_vba_tokenize_code()
    print(txt)