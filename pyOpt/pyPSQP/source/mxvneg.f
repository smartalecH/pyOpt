* SUBROUTINE MXVNEG                ALL SYSTEMS                88/12/01
* PORTABILITY : ALL SYSTEMS
* 88/12/01 LU : ORIGINAL VERSION
*
* PURPOSE :
* CHANGE THE SIGNS OF VECTOR ELEMENTS.
*
* PARAMETERS :
*  II  N  VECTOR DIMENSION.
*  RI  X(N)  INPUT VECTOR.
*  RO  Y(N)  OUTPUT VECTOR WHERE Y:= - X.
*
      SUBROUTINE MXVNEG(N,X,Y)
      INTEGER N
      DOUBLE PRECISION X(*),Y(*)
      INTEGER I
      DO 10 I = 1,N
          Y(I) = -X(I)
   10 CONTINUE
      RETURN
      END