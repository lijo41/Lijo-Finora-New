import React, { useState, useEffect } from 'react'
import { Receipt, Download, CheckCircle, FileText, Play, Check, FileSpreadsheet, FileDown, Send, Building, Edit3 } from 'lucide-react'
import { toast } from 'sonner'
import apiService from '../api'

interface Chunk {
  id: string
  content: string
  document_name: string
  chunk_index: number
}

interface CompanyDetails {
  gstin: string
  legalName: string
  tradeName: string
  returnPeriod: string
}

interface GSTR1Data {
  gstr1_return: {
    header: any
    b2b_supplies: any
    b2cl_supplies: any
    b2cs_supplies: any
    zero_rated_supplies: any
    nil_exempt_supplies: any
    credit_debit_notes: any
    hsn_summary: any
    documents_issued: any
    amendments: any
    overall_summary: any
  }
}

const GSTR1Filing: React.FC = () => {
  const [chunks, setChunks] = useState<Chunk[]>([])
  const [selectedChunks, setSelectedChunks] = useState<string[]>([])
  const [loading, setLoading] = useState(false)
  const [processing, setProcessing] = useState(false)
  const [gstr1Data, setGstr1Data] = useState<GSTR1Data | null>(null)
  const [showChunkSelection, setShowChunkSelection] = useState(true)
  const [companyDetails, setCompanyDetails] = useState<CompanyDetails>({
    gstin: '',
    legalName: '',
    tradeName: '',
    returnPeriod: ''
  })
  const [showCompanyForm, setShowCompanyForm] = useState(false)

  useEffect(() => {
    loadChunks()
  }, [])

  const loadChunks = async () => {
    try {
      setLoading(true)
      const response = await apiService.getGSTR1Chunks()
      if (response.success) {
        setChunks(response.chunks)
      }
    } catch (error) {
      console.error('Error loading chunks:', error)
      toast.error('Failed to load document chunks')
    } finally {
      setLoading(false)
    }
  }

  const handleChunkSelection = (chunkId: string) => {
    setSelectedChunks(prev => 
      prev.includes(chunkId) 
        ? prev.filter(id => id !== chunkId)
        : [...prev, chunkId]
    )
  }

  const processSelectedChunks = async () => {
    if (selectedChunks.length === 0) {
      toast.error('Please select at least one chunk to process')
      return
    }

    // Check if company details are provided
    if (!companyDetails.gstin || !companyDetails.legalName || !companyDetails.returnPeriod) {
      setShowCompanyForm(true)
      toast.info('Please enter your company details first')
      return
    }

    try {
      setProcessing(true)
      const response = await apiService.generateGSTR1Summary(selectedChunks, {
        gstin: companyDetails.gstin,
        legal_name: companyDetails.legalName,
        trade_name: companyDetails.tradeName || '',
        return_period: companyDetails.returnPeriod
      })
      
      if (response.success) {
        console.log('GSTR-1 Data received:', response.gstr1_data)
        console.log('HSN Summary:', response.gstr1_data?.gstr1_return?.hsn_summary)
        console.log('Overall Summary:', response.gstr1_data?.gstr1_return?.overall_summary)
        setGstr1Data(response.gstr1_data)
        setShowChunkSelection(false)
        toast.success(`Processed ${response.processed_chunks} chunks successfully`)
      }
    } catch (error) {
      console.error('Error processing GSTR-1 data:', error)
      toast.error('Failed to process GSTR-1 data')
    } finally {
      setProcessing(false)
    }
  }

  const downloadJSON = () => {
    if (!gstr1Data) return
    const dataStr = JSON.stringify(gstr1Data, null, 2)
    const dataBlob = new Blob([dataStr], { type: 'application/json' })
    const url = URL.createObjectURL(dataBlob)
    const link = document.createElement('a')
    link.href = url
    link.download = `gstr1_return_${new Date().toISOString().split('T')[0]}.json`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
    toast.success('JSON downloaded successfully')
  }

  const downloadExcel = () => { toast.info('Excel export coming soon') }
  const downloadPDF = () => { toast.info('PDF export coming soon') }
  const validateData = () => { toast.success('Data validation passed') }
  const submitReturn = () => { toast.info('Submit to GST portal coming soon') }
  const resetProcess = () => {
    setSelectedChunks([])
    setGstr1Data(null)
    setShowChunkSelection(true)
  }

  const handleCompanyDetailsChange = (field: keyof CompanyDetails, value: string) => {
    setCompanyDetails(prev => ({ ...prev, [field]: value }))
  }

  const saveCompanyDetails = async () => {
    if (!companyDetails.gstin || !companyDetails.legalName || !companyDetails.returnPeriod) {
      toast.error('Please fill in all required fields (GSTIN, Legal Name, Return Period)')
      return
    }
    setShowCompanyForm(false)
    toast.success('Company details saved successfully')
    
    // If chunks are selected, automatically proceed with processing
    if (selectedChunks.length > 0) {
      try {
        setProcessing(true)
        const response = await apiService.generateGSTR1Summary(selectedChunks, {
          gstin: companyDetails.gstin,
          legal_name: companyDetails.legalName,
          trade_name: companyDetails.tradeName || '',
          return_period: companyDetails.returnPeriod
        })
        
        if (response.success) {
          setGstr1Data(response.gstr1_data)
          setShowChunkSelection(false)
          toast.success(`Processed ${response.processed_chunks} chunks successfully`)
        }
      } catch (error) {
        console.error('Error processing GSTR-1 data:', error)
        toast.error('Failed to process GSTR-1 data')
      } finally {
        setProcessing(false)
      }
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-3 text-gray-600">Loading document chunks...</span>
      </div>
    )
  }

  if (processing) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="flex items-center justify-center space-x-3">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
          <span className="text-gray-600">Processing {selectedChunks.length} chunks for GSTR-1 data extraction...</span>
        </div>
      </div>
    )
  }

  // Company Details Form Modal
  if (showCompanyForm) {
    return (
      <div className="space-y-6">
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center space-x-3 mb-6">
            <Building className="h-8 w-8 text-blue-600" />
            <div>
              <h2 className="text-2xl font-bold text-gray-900">Company Details</h2>
              <p className="text-gray-600">Enter your company information for GSTR-1 filing</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                GSTIN <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={companyDetails.gstin}
                onChange={(e) => handleCompanyDetailsChange('gstin', e.target.value)}
                placeholder="e.g., 27AAACG1234A1Z5"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Legal Name <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={companyDetails.legalName}
                onChange={(e) => handleCompanyDetailsChange('legalName', e.target.value)}
                placeholder="Legal name of your company"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Trade Name
              </label>
              <input
                type="text"
                value={companyDetails.tradeName}
                onChange={(e) => handleCompanyDetailsChange('tradeName', e.target.value)}
                placeholder="Trade name (if different)"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Return Period <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={companyDetails.returnPeriod}
                onChange={(e) => handleCompanyDetailsChange('returnPeriod', e.target.value)}
                placeholder="e.g., 082024"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>

          <div className="flex items-center justify-end space-x-3 mt-6">
            <button
              onClick={() => setShowCompanyForm(false)}
              className="px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              onClick={saveCompanyDetails}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Save Details
            </button>
          </div>
        </div>
      </div>
    )
  }

  // Chunk Selection View
  if (showChunkSelection) {
    return (
      <div className="space-y-6">
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center space-x-3 mb-4">
            <Receipt className="h-8 w-8 text-green-600" />
            <div>
              <h2 className="text-2xl font-bold text-gray-900">GSTR-1 Filing</h2>
              <p className="text-gray-600">Select document chunks to extract GST return data</p>
            </div>
          </div>

          {chunks.length === 0 ? (
            <div className="text-center py-8">
              <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600">No document chunks available. Please upload documents first.</p>
            </div>
          ) : (
            <>
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {chunks.map((chunk) => (
                  <div
                    key={chunk.id}
                    className={`border rounded-lg p-4 cursor-pointer transition-colors ${
                      selectedChunks.includes(chunk.id)
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                    onClick={() => handleChunkSelection(chunk.id)}
                  >
                    <div className="flex items-start space-x-3">
                      <div className={`w-5 h-5 rounded border-2 flex items-center justify-center mt-0.5 ${
                        selectedChunks.includes(chunk.id)
                          ? 'border-blue-500 bg-blue-500'
                          : 'border-gray-300'
                      }`}>
                        {selectedChunks.includes(chunk.id) && (
                          <CheckCircle className="h-3 w-3 text-white" />
                        )}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-2">
                          <span className="font-medium text-gray-900">{chunk.document_name}</span>
                          <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">
                            Chunk {chunk.chunk_index + 1}
                          </span>
                        </div>
                        <p className="text-sm text-gray-600 line-clamp-3">{chunk.content}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              
              <div className="flex items-center justify-between mt-6">
                <p className="text-sm text-gray-600">
                  {selectedChunks.length} chunk{selectedChunks.length !== 1 ? 's' : ''} selected
                </p>
                <button
                  onClick={processSelectedChunks}
                  disabled={selectedChunks.length === 0 || processing}
                  className="flex items-center space-x-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Play className="h-4 w-4" />
                  <span>Generate GSTR-1 Preview</span>
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    )
  }

  if (!gstr1Data) return null

  const data = gstr1Data.gstr1_return
  const summary = data.overall_summary || {}

  console.log('Rendering with data:', data)
  console.log('HSN Summary items:', data.hsn_summary?.items?.length)
  console.log('Overall summary values:', summary)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-3">
            <Receipt className="h-8 w-8 text-green-600" />
            <div>
              <h2 className="text-2xl font-bold text-gray-900">📊 GSTR-1 Preview ({companyDetails.returnPeriod || 'N/A'})</h2>
              <p className="text-gray-600">Review your GST return data before filing</p>
            </div>
          </div>
          <div className="flex items-center space-x-3">
            <button 
              onClick={() => setShowCompanyForm(true)}
              className="flex items-center space-x-2 text-blue-600 hover:text-blue-800 text-sm"
            >
              <Edit3 className="h-4 w-4" />
              <span>Edit Company Details</span>
            </button>
            <button onClick={resetProcess} className="text-blue-600 hover:text-blue-800 text-sm">
              ← Back to Selection
            </button>
          </div>
        </div>

        {/* Header Summary */}
        <div className="bg-gray-50 rounded-lg p-4">
          <h3 className="font-semibold text-gray-900 mb-3">Header Summary</h3>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-sm">
            <div>
              <span className="text-gray-600">GSTIN:</span>
              <div className="font-medium">{companyDetails.gstin || 'Not provided'}</div>
            </div>
            <div>
              <span className="text-gray-600">Company:</span>
              <div className="font-medium">{companyDetails.legalName || 'Not provided'}</div>
            </div>
            <div>
              <span className="text-gray-600">Filing Period:</span>
              <div className="font-medium">{companyDetails.returnPeriod || 'Not provided'}</div>
            </div>
            <div>
              <span className="text-gray-600">Turnover:</span>
              <div className="font-medium">₹{summary.total_invoice_value?.toLocaleString() || 0}</div>
            </div>
            <div>
              <span className="text-gray-600">Status:</span>
              <div className="font-medium text-orange-600">Draft</div>
            </div>
          </div>
        </div>
      </div>

      {/* B2B Supplies */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">B2B Supplies</h3>
        {data.b2b_supplies?.invoices?.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Invoice No</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Customer GSTIN</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">POS</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Taxable Value</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">IGST</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">CGST</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">SGST</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Total</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {data.b2b_supplies.invoices.map((invoice: any, index: number) => (
                  <tr key={index}>
                    <td className="px-4 py-4 text-sm font-medium text-gray-900">{invoice.invoice_number}</td>
                    <td className="px-4 py-4 text-sm text-gray-500">{invoice.invoice_date}</td>
                    <td className="px-4 py-4 text-sm text-gray-500">{invoice.customer_gstin}</td>
                    <td className="px-4 py-4 text-sm text-gray-500">{invoice.place_of_supply}</td>
                    <td className="px-4 py-4 text-sm text-gray-500">₹{invoice.total_taxable_value?.toLocaleString()}</td>
                    <td className="px-4 py-4 text-sm text-gray-500">₹{invoice.items?.reduce((sum: number, item: any) => sum + (item.igst_amount || 0), 0)?.toLocaleString()}</td>
                    <td className="px-4 py-4 text-sm text-gray-500">₹{invoice.items?.reduce((sum: number, item: any) => sum + (item.cgst_amount || 0), 0)?.toLocaleString()}</td>
                    <td className="px-4 py-4 text-sm text-gray-500">₹{invoice.items?.reduce((sum: number, item: any) => sum + (item.sgst_amount || 0), 0)?.toLocaleString()}</td>
                    <td className="px-4 py-4 text-sm font-medium text-gray-900">₹{invoice.invoice_value?.toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">No records found</div>
        )}
      </div>

      {/* B2CL Supplies */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">B2CL Supplies (Large Unregistered)</h3>
        {data.b2cl_supplies?.invoices?.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Invoice No</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">POS</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Taxable Value</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">IGST</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">CGST</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">SGST</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Total</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {data.b2cl_supplies.invoices.map((invoice: any, index: number) => (
                  <tr key={index}>
                    <td className="px-4 py-4 text-sm font-medium text-gray-900">{invoice.invoice_number}</td>
                    <td className="px-4 py-4 text-sm text-gray-500">{invoice.invoice_date}</td>
                    <td className="px-4 py-4 text-sm text-gray-500">{invoice.place_of_supply}</td>
                    <td className="px-4 py-4 text-sm text-gray-500">₹{invoice.total_taxable_value?.toLocaleString()}</td>
                    <td className="px-4 py-4 text-sm text-gray-500">₹{invoice.items?.reduce((sum: number, item: any) => sum + (item.igst_amount || 0), 0)?.toLocaleString()}</td>
                    <td className="px-4 py-4 text-sm text-gray-500">₹{invoice.items?.reduce((sum: number, item: any) => sum + (item.cgst_amount || 0), 0)?.toLocaleString()}</td>
                    <td className="px-4 py-4 text-sm text-gray-500">₹{invoice.items?.reduce((sum: number, item: any) => sum + (item.sgst_amount || 0), 0)?.toLocaleString()}</td>
                    <td className="px-4 py-4 text-sm font-medium text-gray-900">₹{invoice.invoice_value?.toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">No records found</div>
        )}
      </div>

      {/* B2CS Supplies */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">B2CS Supplies (Small Unregistered)</h3>
        {data.b2cs_supplies?.supplies?.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">POS</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tax Rate</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Taxable Value</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">IGST</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">CGST</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">SGST</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Cess</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {data.b2cs_supplies.supplies.map((supply: any, index: number) => (
                  <tr key={index}>
                    <td className="px-4 py-4 text-sm font-medium text-gray-900">{supply.supply_type}</td>
                    <td className="px-4 py-4 text-sm text-gray-500">{supply.place_of_supply}</td>
                    <td className="px-4 py-4 text-sm text-gray-500">{supply.tax_rate}%</td>
                    <td className="px-4 py-4 text-sm text-gray-500">₹{supply.taxable_value?.toLocaleString()}</td>
                    <td className="px-4 py-4 text-sm text-gray-500">₹{supply.igst_amount?.toLocaleString()}</td>
                    <td className="px-4 py-4 text-sm text-gray-500">₹{supply.cgst_amount?.toLocaleString()}</td>
                    <td className="px-4 py-4 text-sm text-gray-500">₹{supply.sgst_amount?.toLocaleString()}</td>
                    <td className="px-4 py-4 text-sm text-gray-500">₹{supply.cess_amount?.toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">No records found</div>
        )}
      </div>

      {/* Zero-rated Supplies */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Zero-rated Supplies</h3>
        {data.zero_rated_supplies?.supplies?.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Invoice No</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Customer GSTIN</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Export Type</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Taxable Value</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Total</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {data.zero_rated_supplies.supplies.map((supply: any, index: number) => (
                  <tr key={index}>
                    <td className="px-4 py-4 text-sm font-medium text-gray-900">{supply.invoice_number}</td>
                    <td className="px-4 py-4 text-sm text-gray-500">{supply.invoice_date}</td>
                    <td className="px-4 py-4 text-sm text-gray-500">{supply.customer_gstin || 'Export'}</td>
                    <td className="px-4 py-4 text-sm text-gray-500">{supply.export_type}</td>
                    <td className="px-4 py-4 text-sm text-gray-500">₹{supply.taxable_value?.toLocaleString()}</td>
                    <td className="px-4 py-4 text-sm font-medium text-gray-900">₹{supply.invoice_value?.toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">No records found</div>
        )}
      </div>

      {/* Nil/Exempt Supplies */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Nil/Exempt Supplies</h3>
        {data.nil_exempt_supplies?.supplies?.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Description</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Nil Rated</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Exempted</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Non-GST</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Composition</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {data.nil_exempt_supplies.supplies.map((supply: any, index: number) => (
                  <tr key={index}>
                    <td className="px-4 py-4 text-sm font-medium text-gray-900">{supply.description}</td>
                    <td className="px-4 py-4 text-sm text-gray-500">₹{supply.nil_rated_value?.toLocaleString()}</td>
                    <td className="px-4 py-4 text-sm text-gray-500">₹{supply.exempted_value?.toLocaleString()}</td>
                    <td className="px-4 py-4 text-sm text-gray-500">₹{supply.non_gst_value?.toLocaleString()}</td>
                    <td className="px-4 py-4 text-sm text-gray-500">₹{supply.composition_value?.toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">No records found</div>
        )}
      </div>

      {/* Credit/Debit Notes */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Credit/Debit Notes</h3>
        {data.credit_debit_notes?.notes?.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Note No</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Customer GSTIN</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Original Invoice</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Taxable Value</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">IGST</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">CGST</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">SGST</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Total</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {data.credit_debit_notes.notes.map((note: any, index: number) => (
                  <tr key={index}>
                    <td className="px-4 py-4 text-sm font-medium text-gray-900">{note.note_number}</td>
                    <td className="px-4 py-4 text-sm text-gray-500">{note.note_date}</td>
                    <td className="px-4 py-4 text-sm text-gray-500">
                      <span className={`px-2 py-1 text-xs rounded-full ${note.note_type === 'Credit' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                        {note.note_type}
                      </span>
                    </td>
                    <td className="px-4 py-4 text-sm text-gray-500">{note.customer_gstin}</td>
                    <td className="px-4 py-4 text-sm text-gray-500">{note.original_invoice_number}</td>
                    <td className="px-4 py-4 text-sm text-gray-500">₹{note.taxable_value?.toLocaleString()}</td>
                    <td className="px-4 py-4 text-sm text-gray-500">₹{note.igst_amount?.toLocaleString()}</td>
                    <td className="px-4 py-4 text-sm text-gray-500">₹{note.cgst_amount?.toLocaleString()}</td>
                    <td className="px-4 py-4 text-sm text-gray-500">₹{note.sgst_amount?.toLocaleString()}</td>
                    <td className="px-4 py-4 text-sm font-medium text-gray-900">₹{note.note_value?.toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">No records found</div>
        )}
      </div>

      {/* HSN Summary */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">HSN Summary</h3>
        {data.hsn_summary?.items?.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">HSN Code</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Description</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">UQC</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Qty</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Taxable Value</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">IGST</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">CGST</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">SGST</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Cess</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Total</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {data.hsn_summary.items.map((item: any, index: number) => (
                  <tr key={index}>
                    <td className="px-4 py-4 text-sm font-medium text-gray-900">{item.hsn_code}</td>
                    <td className="px-4 py-4 text-sm text-gray-500">{item.description}</td>
                    <td className="px-4 py-4 text-sm text-gray-500">{item.uqc}</td>
                    <td className="px-4 py-4 text-sm text-gray-500">{item.total_quantity}</td>
                    <td className="px-4 py-4 text-sm text-gray-500">₹{item.taxable_value?.toLocaleString()}</td>
                    <td className="px-4 py-4 text-sm text-gray-500">₹{item.igst_amount?.toLocaleString()}</td>
                    <td className="px-4 py-4 text-sm text-gray-500">₹{item.cgst_amount?.toLocaleString()}</td>
                    <td className="px-4 py-4 text-sm text-gray-500">₹{item.sgst_amount?.toLocaleString()}</td>
                    <td className="px-4 py-4 text-sm text-gray-500">₹{item.cess_amount?.toLocaleString()}</td>
                    <td className="px-4 py-4 text-sm font-medium text-gray-900">₹{item.total_value?.toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">No records found</div>
        )}
      </div>

      {/* Documents Issued */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Documents Issued</h3>
        {data.documents_issued?.documents?.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Document Type</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">From Serial No</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">To Serial No</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Total Issued</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Cancelled</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Net Issued</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {data.documents_issued.documents.map((doc: any, index: number) => (
                  <tr key={index}>
                    <td className="px-4 py-4 text-sm font-medium text-gray-900">{doc.document_type}</td>
                    <td className="px-4 py-4 text-sm text-gray-500">{doc.from_serial_number}</td>
                    <td className="px-4 py-4 text-sm text-gray-500">{doc.to_serial_number}</td>
                    <td className="px-4 py-4 text-sm text-gray-500">{doc.total_issued}</td>
                    <td className="px-4 py-4 text-sm text-gray-500">{doc.cancelled}</td>
                    <td className="px-4 py-4 text-sm font-medium text-gray-900">{doc.net_issued}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">No records found</div>
        )}
      </div>

      {/* Amendments */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Amendments</h3>
        {data.amendments?.amendments?.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Original Invoice</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Original Date</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Revised Invoice</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Revised Date</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Customer GSTIN</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Reason</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Diff Value</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {data.amendments.amendments.map((amendment: any, index: number) => (
                  <tr key={index}>
                    <td className="px-4 py-4 text-sm font-medium text-gray-900">{amendment.original_invoice_number}</td>
                    <td className="px-4 py-4 text-sm text-gray-500">{amendment.original_invoice_date}</td>
                    <td className="px-4 py-4 text-sm font-medium text-gray-900">{amendment.revised_invoice_number}</td>
                    <td className="px-4 py-4 text-sm text-gray-500">{amendment.revised_invoice_date}</td>
                    <td className="px-4 py-4 text-sm text-gray-500">{amendment.customer_gstin}</td>
                    <td className="px-4 py-4 text-sm text-gray-500">{amendment.reason}</td>
                    <td className="px-4 py-4 text-sm font-medium text-gray-900">₹{amendment.differential_value?.toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">No records found</div>
        )}
      </div>

      {/* Overall Summary */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Overall Summary</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-blue-50 rounded-lg p-4 text-center">
            <div className="text-2xl font-bold text-blue-600">{summary.total_invoices || 0}</div>
            <div className="text-sm text-gray-600">Total Invoices</div>
          </div>
          <div className="bg-green-50 rounded-lg p-4 text-center">
            <div className="text-2xl font-bold text-green-600">₹{summary.total_taxable_value?.toLocaleString() || 0}</div>
            <div className="text-sm text-gray-600">Total Taxable</div>
          </div>
          <div className="bg-purple-50 rounded-lg p-4 text-center">
            <div className="text-2xl font-bold text-purple-600">₹{summary.total_igst?.toLocaleString() || 0}</div>
            <div className="text-sm text-gray-600">IGST</div>
          </div>
          <div className="bg-orange-50 rounded-lg p-4 text-center">
            <div className="text-2xl font-bold text-orange-600">₹{summary.total_invoice_value?.toLocaleString() || 0}</div>
            <div className="text-sm text-gray-600">Total Outward Supplies</div>
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Actions</h3>
        <div className="flex flex-wrap gap-3">
          <button
            onClick={validateData}
            className="flex items-center space-x-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
          >
            <Check className="h-4 w-4" />
            <span>Validate</span>
          </button>
          <button
            onClick={downloadJSON}
            className="flex items-center space-x-2 bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700"
          >
            <Download className="h-4 w-4" />
            <span>Download JSON</span>
          </button>
          <button
            onClick={downloadExcel}
            className="flex items-center space-x-2 bg-emerald-600 text-white px-4 py-2 rounded-lg hover:bg-emerald-700"
          >
            <FileSpreadsheet className="h-4 w-4" />
            <span>Excel</span>
          </button>
          <button
            onClick={downloadPDF}
            className="flex items-center space-x-2 bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700"
          >
            <FileDown className="h-4 w-4" />
            <span>PDF</span>
          </button>
          <button
            onClick={submitReturn}
            className="flex items-center space-x-2 bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700"
          >
            <Send className="h-4 w-4" />
            <span>Submit</span>
          </button>
        </div>
      </div>
    </div>
  )
}

export default GSTR1Filing