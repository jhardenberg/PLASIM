/* Exercise MoSt's real input readers without creating an X display. */
#define main most_program_main
#include "most.c"
#undef main

int main(int argc, char **argv)
{
   double *grid;
   int i;

   if (argc != 3) return 2;
   if (!strcmp(argv[1], "timing"))
   {
      struct SelStruct timing[2] = {{0}};
      int found = 0;
      InitNamelist();
      for (i = 0; i < NL_items; ++i)
      {
         if (NL_list[i].model == PLASIM &&
             (!strcmp(NL_list[i].name, "MPSTEP") ||
              !strcmp(NL_list[i].name, "NAOMOD")))
         {
            if (found >= 2) return 6;
            timing[found].Item = &NL_list[i];
            timing[found].type = SEL_INT;
            timing[found].iv = NL_list[i].ival;
            strcpy(timing[found].text, NL_list[i].name);
            found++;
         }
      }
      if (found != 2) return 6;
      ComEnd = &SelStart;
      SelStart.Next = &timing[0];
      timing[0].Next = &timing[1];
      Model = PLASIM;
      Planet = EARTH;
      Lsg = Oce = Cores = Multirun = 1;
      Resolution = atoi(argv[2]);
      if (Resolution < 1 || Resolution >= RESOLUTIONS) return 7;
      CheckPlasimNamelist();
      for (i = 0; i < 2; ++i) sprintf(timing[i].teva, "%d", timing[i].iv);
      WriteNamelistFile("plasim", 0);
      WriteNamelistFile("oceanmod", 0);
   }
   else if (!strcmp(argv[1], "settings"))
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
