/* Exercise MoSt's real input readers without creating an X display. */
#define main most_program_main
#include "most.c"
#undef main

int main(int argc, char **argv)
{
   double *grid;
   int i;

   if (argc != 3) return 2;
   if (!strcmp(argv[1], "settings"))
   {
      strcpy(SelStart.text, "TEST");
      SelStart.type = SEL_INT;
      SelStart.iv = -1;
      printf("READ=%d\n", ReadSettings(argv[2]));
      printf("VALUE=%d\n", SelStart.iv);
   }
   else
   {
      int latitudes = !strcmp(argv[1], "reference32") ? 32 :
                      !strcmp(argv[1], "reference64") ? 64 : 4;
      grid = ReadGrid(argv[2], latitudes, 2.0);
      if (!grid) return 3;
      for (i = 0; i < latitudes; ++i)
      {
         int j;
         int stride = 2*latitudes + 1;
         for (j = 0; j < 2*latitudes; ++j)
         {
            if (!isfinite(grid[j + i*stride])) return 4;
            if (latitudes == 4 && grid[j + i*stride] != 2.0 * (j + i*8 + 1)) return 4;
         }
         if (grid[i*stride + 2*latitudes] != grid[i*stride]) return 5;
      }
      free(grid);
   }
   return 0;
}
