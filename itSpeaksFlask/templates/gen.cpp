#include <bits/stdc++.h>
using namespace std;
char str[25];
int main(){
	FILE *fp;
	FILE *fp1;
	fp=fopen("temp.txt", "r");
	fp1=fopen("out.txt", "w");
	while(fscanf(fp,"%s", str)!=EOF){
		fprintf(fp1, "\t\t\t\t<div>\n");
		fprintf(fp1, "\t\t\t\t\t<input type=\"checkbox\" id=\"%s\" name=\"interest\" value=\"%s\">\n", str, str);
		fprintf(fp1, "\t\t\t\t\t<label for=\"%s\">%s</label>\n", str, str);
		fprintf(fp1, "\t\t\t\t</div>\n");
	}
}
