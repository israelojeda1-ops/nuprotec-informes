# Columnas de iw_gsaen (encabezado de ventas / facturas)

| # | Columna | Tipo | Largo | Nulable |
|---|---------|------|-------|--------|
| 1 | Tipo | varchar | 1.0 | NO |
| 2 | NroInt | int |  | NO |
| 3 | CodBode | varchar | 10.0 | YES |
| 4 | CodCaja | varchar | 3.0 | YES |
| 5 | Folio | decimal |  | YES |
| 6 | Concepto | varchar | 2.0 | YES |
| 7 | Estado | varchar | 1.0 | NO |
| 8 | Fecha | datetime |  | YES |
| 9 | FechaVenc | datetime |  | YES |
| 10 | Glosa | varchar | 255.0 | YES |
| 11 | Orden | int |  | YES |
| 12 | Factura | decimal |  | YES |
| 13 | AuxTipo | varchar | 1.0 | NO |
| 14 | CodAux | varchar | 10.0 | YES |
| 15 | CodiCC | varchar | 8.0 | YES |
| 16 | CodBod | varchar | 10.0 | YES |
| 17 | AuxGuiaNum | decimal |  | YES |
| 18 | AuxGuiaFec | datetime |  | YES |
| 19 | AuxDocNum | decimal |  | YES |
| 20 | AuxDocfec | datetime |  | YES |
| 21 | CodLugarDesp | varchar | 30.0 | YES |
| 22 | CodListaPrecio | varchar | 3.0 | YES |
| 23 | CodReserva | varchar | 10.0 | YES |
| 24 | CodVendedor | varchar | 4.0 | YES |
| 25 | CodMoneda | varchar | 2.0 | YES |
| 26 | Equivalencia | float |  | YES |
| 27 | Patente | varchar | 9.0 | YES |
| 28 | RetiradoPor | varchar | 30.0 | YES |
| 29 | Usuario | varchar | 8.0 | YES |
| 30 | NetoAfecto | float |  | YES |
| 31 | NetoExento | float |  | YES |
| 32 | IVA | float |  | YES |
| 33 | PorcDesc01 | float |  | YES |
| 34 | Descto01 | float |  | YES |
| 35 | PorcDesc02 | float |  | YES |
| 36 | Descto02 | float |  | YES |
| 37 | PorcDesc03 | float |  | YES |
| 38 | Descto03 | float |  | YES |
| 39 | PorcDesc04 | float |  | YES |
| 40 | Descto04 | float |  | YES |
| 41 | PorcDesc05 | float |  | YES |
| 42 | Descto05 | float |  | YES |
| 43 | TotalDesc | float |  | YES |
| 44 | Flete | float |  | YES |
| 45 | Embalaje | float |  | YES |
| 46 | Total | float |  | YES |
| 47 | StockActualizado | int |  | YES |
| 48 | EnMantencion | int |  | YES |
| 49 | Cuenta | varchar | 18.0 | YES |
| 50 | CentroDeCosto | varchar | 8.0 | YES |
| 51 | SubTotal | float |  | YES |
| 52 | CondPago | varchar | 3.0 | YES |
| 53 | ContabVenta | int |  | YES |
| 54 | ContabCosto | int |  | YES |
| 55 | ContDespPend | int |  | YES |
| 56 | ContConsumo | int |  | YES |
| 57 | ContVtaComp | int |  | YES |
| 58 | SolicitadoPor | varchar | 30.0 | YES |
| 59 | DespachadoPor | varchar | 30.0 | YES |
| 60 | NomAux | varchar | 60.0 | YES |
| 61 | RutAux | varchar | 20.0 | YES |
| 62 | ComAux | varchar | 4.0 | YES |
| 63 | CiuAux | varchar | 3.0 | YES |
| 64 | PaiAux | varchar | 3.0 | YES |
| 65 | DirAux | varchar | 60.0 | YES |
| 66 | FonAux | varchar | 15.0 | YES |
| 67 | FaxAux | varchar | 15.0 | YES |
| 68 | ComDch | varchar | 7.0 | YES |
| 69 | CiuDch | varchar | 3.0 | YES |
| 70 | PaiDch | varchar | 3.0 | YES |
| 71 | AtDch | varchar | 15.0 | YES |
| 72 | DirDch | varchar | 60.0 | YES |
| 73 | Sistema | varchar | 2.0 | YES |
| 74 | Proceso | varchar | 30.0 | YES |
| 75 | nvnumero | int |  | YES |
| 76 | ContabPago | int |  | YES |
| 77 | NumGuiaTrasp | decimal |  | YES |
| 78 | FueExportado | int |  | YES |
| 79 | Id_Paquete | varchar | 30.0 | YES |
| 80 | NroVale | int |  | YES |
| 81 | CanCod | varchar | 3.0 | YES |
| 82 | esDevolucion | int |  | YES |
| 83 | CWCpbAno | varchar | 4.0 | YES |
| 84 | CWCpbNum | varchar | 8.0 | YES |
| 85 | SubTipoDocto | varchar | 1.0 | NO |
| 86 | MarcaWG | int |  | YES |
| 87 | CpbAnoDespP | varchar | 4.0 | YES |
| 88 | CpbNumDespP | varchar | 9.0 | YES |
| 89 | CpbAnoPagos | varchar | 4.0 | YES |
| 90 | CpbNumPagos | varchar | 9.0 | YES |
| 91 | Cod_Distrib | varchar | 10.0 | YES |
| 92 | Nom_Distrib | varchar | 60.0 | YES |
| 93 | FecHoraCreacion | datetime |  | YES |
| 94 | ListaMayorista | int |  | YES |
| 95 | BoletaFiscal | int |  | YES |
| 96 | ImpresaOk | int |  | YES |
| 97 | CpbAnoVentas | varchar | 4.0 | YES |
| 98 | CpbNumVentas | varchar | 9.0 | YES |
| 99 | CpbAnoCostos | varchar | 4.0 | YES |
| 100 | CpbNumCostos | varchar | 9.0 | YES |
| 101 | CpbAnoConsumos | varchar | 4.0 | YES |
| 102 | CpbNumConsumos | varchar | 9.0 | YES |
| 103 | ContabenPW | int |  | YES |
| 104 | TtdCod | varchar | 2.0 | YES |
| 105 | RutSolicitante | varchar | 20.0 | YES |
| 106 | RutTransportista | varchar | 20.0 | YES |
| 107 | TipDocRef | varchar | 1.0 | YES |
| 108 | SubTipDocRef | varchar | 1.0 | YES |
| 109 | DescLisPreenMov | int |  | YES |
| 110 | MotivoNCND | int |  | YES |
| 111 | CorrelativoAprobacion | float |  | YES |
| 112 | CpbAnoCompras | varchar | 4.0 | YES |
| 113 | CpbNumCompras | varchar | 9.0 | YES |
| 114 | DTE_SiiTDoc | int |  | YES |
| 115 | ContabenCW | int |  | YES |
| 116 | FactorCostoImportacion | float |  | YES |
| 117 | CodConvenio | varchar | 20.0 | YES |
| 118 | FechaEmisConv | datetime |  | YES |
| 119 | TipoDespacho | int |  | YES |
| 120 | TotalDescBoleta | float |  | YES |
| 121 | CpbAnoCostosIFRS | varchar | 4.0 | YES |
| 122 | CpbNumCostosIFRS | varchar | 9.0 | YES |
| 123 | CpbAnoConsumosIFRS | varchar | 4.0 | YES |
| 124 | CpbNumConsumosIFRS | varchar | 9.0 | YES |
| 125 | CpbAnoComprasIFRS | varchar | 4.0 | YES |
| 126 | CpbNumComprasIFRS | varchar | 9.0 | YES |
| 127 | OtroRUT | varchar | 10.0 | YES |
| 128 | DondeDice | varchar | 255.0 | YES |
| 129 | DebeDecir | varchar | 255.0 | YES |
| 130 | TipoServicioSII | int |  | YES |
| 131 | CpbAnoTomaInv | varchar | 4.0 | YES |
| 132 | CpbNumTomaInv | varchar | 9.0 | YES |
| 133 | FecHoraCreacionVW | datetime |  | YES |
| 134 | NroIntDctoRefAut | int |  | YES |
| 135 | TipoDctoRefAut | varchar | 1.0 | YES |
| 136 | PorcCredEmpConst | float |  | NO |
| 137 | DescCredEmpConst | float |  | NO |
| 138 | PagoConTarjeta | int |  | NO |
| 139 | IDLectorTarjeta | varchar | 50.0 | YES |
| 140 | NetoAfectoLF | float |  | YES |
| 141 | NetoExentoLF | float |  | YES |
| 142 | IVALF | float |  | YES |
| 143 | TotalLF | float |  | YES |
| 144 | FechaIniLF | datetime |  | YES |
| 145 | FechaFinLF | datetime |  | YES |
| 146 | NroPicking | int |  | YES |
| 147 | ComprobantePago | float |  | YES |
| 148 | CodLugarDocto | varchar | 30.0 | YES |
| 149 | TipoTrans | int |  | NO |
| 150 | FmaPago | int |  | NO |
| 151 | NroEmbarque | varchar | 30.0 | YES |
| 152 | EsImportacion | int |  | NO |
| 153 | CodAuxMandante | varchar | 10.0 | YES |
| 154 | NomContacto | varchar | 30.0 | YES |
| 155 | FechaGenDTE | datetime |  | YES |
| 156 | Recargo | float |  | NO |
| 157 | PorRecargo | float |  | NO |
| 158 | RecargoConIva | float |  | NO |
| 159 | CtaRecargo | varchar | 18.0 | YES |
| 160 | NroDin | float |  | NO |
| 161 | NroImportacion | float |  | NO |
| 162 | TpoTranCompra | int |  | NO |
